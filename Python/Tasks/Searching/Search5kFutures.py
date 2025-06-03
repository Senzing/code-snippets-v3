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
    G2EngineFlags,
    G2Exception,
    G2RetryableException,
    G2UnrecoverableException,
)

engine_config_json = os.getenv("SENZING_ENGINE_CONFIGURATION_JSON", None)


def mock_logger(level, exception, error_rec=None):
    print(f"\n{level}: {exception}", file=sys.stderr)
    if error_rec:
        print(f"{error_rec}", file=sys.stderr)


def search_record(engine, rec_to_search):
    search_response = bytearray()
    engine.searchByAttributes(
        rec_to_search,
        search_response,
        G2EngineFlags.G2_SEARCH_BY_ATTRIBUTES_MINIMAL_ALL,
    )
    return search_response


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
        f"Processed {success:,} searches,"
        f" {int(1000 / (time.time() - prev_time)):,} records per second,"
        f" {error} errors"
    )
    return time.time()


def search_results(result, record, out_file):
    response_str = result.decode()
    response_dict = json.loads(response_str)
    response_entities = response_dict.get("RESOLVED_ENTITIES", None)

    out_file.write("-" * 100 + "\n")
    if response_entities:
        out_file.write(f"Result for {record.rstrip()}:\n\n{response_str}\n\n")
    else:
        out_file.write(f"No result for {record}\n\n")


def futures_search(engine, input_file, output_file):
    prev_time = time.time()
    success_recs = error_recs = 0

    with open(output_file, "w") as out_file:
        with open(input_file, "r") as in_file:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(search_record, engine, record): record
                    for record in itertools.islice(in_file, executor._max_workers)
                }

                while futures:
                    done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                    for f in done:
                        try:
                            result = f.result()
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

                            if success_recs % 10000 == 0:
                                engine_stats(engine)

                            search_results(result, futures[f], out_file)
                        finally:
                            record = in_file.readline()
                            if record:
                                futures[executor.submit(search_record, engine, record)] = record

                            del futures[f]

                print(f"\nSuccessfully searched {success_recs:,} records, with" f" {error_recs:,} errors")
                print(f"Search results are located in: {output_file}")


try:
    g2_engine = G2Engine()
    g2_engine.init("G2Engine", engine_config_json, False)
    futures_search(
        g2_engine,
        "../../../Resources/Data/search-5K.json",
        "../../../Resources/Output/search_file.out",
    )
    g2_engine.destroy()
except G2Exception as err:
    mock_logger("CRITICAL", err)
