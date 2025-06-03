#! /usr/bin/env python3

import concurrent.futures
import itertools
import json
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


def replace_record(engine, rec_to_replace):
    record_dict = json.loads(rec_to_replace)
    data_source = record_dict.get("DATA_SOURCE", None)
    record_id = record_dict.get("RECORD_ID", None)
    engine.replaceRecord(data_source, record_id, rec_to_replace)


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


def record_stats(success, error, prev_time):
    print(
        f"Processed {success:,} replacements,"
        f" {int(1000 / (time.time() - prev_time)):,} records per second,"
        f" {error:,} errors"
    )
    return time.time()


def futures_replace(engine, input_file):
    prev_time = time.time()
    success_recs = error_recs = 0

    with open(input_file, "r") as in_file:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(replace_record, engine, record): record
                for record in itertools.islice(in_file, executor._max_workers)
            }

            while futures:
                done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                for f in done:
                    try:
                        f.result()
                    except (G2BadInputException, json.JSONDecodeError) as err:
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
                        if success_recs % 1000 == 0:
                            prev_time = record_stats(success_recs, error_recs, prev_time)

                        if success_recs % 2500 == 0:
                            engine_stats(engine)
                    finally:
                        record = in_file.readline()
                        if record:
                            futures[executor.submit(replace_record, engine, record)] = record

                        del futures[f]

            print(f"Successfully replaced {success_recs:,} records, with" f" {error_recs:,} errors")


try:
    g2_engine = G2Engine()
    g2_engine.init("G2Engine", engine_config_json, False)
    futures_replace(g2_engine, "../../../Resources/Data/replace-5K.json")
    g2_engine.destroy()
except G2Exception as err:
    mock_logger("CRITICAL", err)
