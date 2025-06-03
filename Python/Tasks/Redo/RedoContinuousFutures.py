#! /usr/bin/env python3

import concurrent.futures
import os
import sys
import time

from senzing import (
    G2BadInputException,
    G2Engine,
    G2Exception,
    G2RetryableException,
    G2UnrecoverableException,
)

engine_config_json = os.getenv("SENZING_ENGINE_CONFIGURATION_JSON", None)


def mock_logger(level, exception, error_rec=None):
    print(f"\n{level}: {exception}", file=sys.stderr)
    if error_rec:
        print(f"{error_rec}", file=sys.stderr)


def get_redo_record(engine):
    try:
        redo_record = bytearray()
        engine.getRedoRecord(redo_record)
    except G2Exception as err:
        mock_logger("CRITICAL", err)
        raise err

    return redo_record.decode()


def prime_redo_records(engine, quantity):
    redo_records = []
    for _ in range(quantity):
        single_redo_rec = get_redo_record(engine)
        if single_redo_rec:
            redo_records.append(single_redo_rec)
    return redo_records


def process_redo_record(engine, record):
    engine.process(record)


def engine_stats(engine):
    response = bytearray()
    try:
        engine.stats(response)
        print(f"\n{response.decode()}\n")
    except G2RetryableException as err:
        mock_logger("WARN", err)
    except G2Exception as err:
        mock_logger("CRITICAL", err)
        raise


def redo_count(engine):
    redo_recs = None
    try:
        redo_recs = engine.countRedoRecords()
    except G2RetryableException as err:
        mock_logger("WARN", err)
    except G2Exception as err:
        mock_logger("CRITICAL", err)
        raise

    return redo_recs


def redo_pause(success):
    print("No redo records to process, pausing for 30 seconds. Total processed:" f" {success:,} (CTRL-C to exit)...")
    time.sleep(30)


def futures_redo(engine):
    success_recs = error_recs = 0
    redo_paused = False

    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            futures = {
                executor.submit(process_redo_record, engine, record): record
                for record in prime_redo_records(engine, executor._max_workers)
            }
            if not futures:
                redo_pause(success_recs)
            else:
                break

        while True:
            done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
            for f in done:
                try:
                    _ = f.result()
                except G2BadInputException as err:
                    mock_logger("ERROR", err, futures[f])
                    error_recs += 1
                except G2RetryableException as err:
                    mock_logger("WARN", err, futures[f])
                    error_recs += 1
                except (G2UnrecoverableException, G2Exception) as err:
                    mock_logger("CRITICAL", err, futures[f])
                    raise
                else:
                    success_recs += 1
                    if success_recs % 100 == 0:
                        print(f"Processed {success_recs:,} redo records, with" f" {error_recs:,} errors")

                    if success_recs % 1000 == 0:
                        engine_stats(engine)
                finally:
                    record = get_redo_record(engine)
                    if record:
                        futures[executor.submit(process_redo_record, engine, record)] = record
                    else:
                        redo_paused = True

                    del futures[f]

            if redo_paused:
                while not redo_count(engine):
                    redo_pause(success_recs)
                redo_paused = False
                while len(futures) < executor._max_workers:
                    record = get_redo_record(engine)
                    if record:
                        futures[executor.submit(process_redo_record, engine, record)] = record


try:
    g2_engine = G2Engine()
    g2_engine.init("G2Engine", engine_config_json, False)
    futures_redo(g2_engine)
    g2_engine.destroy()
except G2Exception as err:
    mock_logger("CRITICAL", err)
