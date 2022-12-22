#! /usr/bin/env python3

import json
import os
import sys
from senzing import G2BadInputException, G2Engine, G2Exception, G2RetryableException, G2UnrecoverableException

engine_config_json = os.getenv('SENZING_ENGINE_CONFIGURATION_JSON', None)


def mock_logger(level, exception, error_rec=None):
    print(f'\n{level}: {exception}', file=sys.stderr)
    if error_rec:
        print(f'{error_rec}', file=sys.stderr)


def add_records_from_file(engine, input_file):
    success_recs = 0

    with open(input_file, 'r') as file:

        for rec_to_add in file:
            try:
                record_dict = json.loads(rec_to_add)
                data_source = record_dict.get('DATA_SOURCE', None)
                record_id = record_dict.get('RECORD_ID', None)
                engine.addRecord(data_source, record_id, rec_to_add)
            except G2BadInputException as ex:
                mock_logger('ERROR', ex, rec_to_add)
            except G2RetryableException as ex:
                mock_logger('WARN', ex, rec_to_add)
            except (G2UnrecoverableException, G2Exception) as ex:
                mock_logger('CRITICAL', ex, rec_to_add)
                raise ex
            except json.JSONDecodeError as ex:
                mock_logger('ERROR', ex, rec_to_add)
            else:
                success_recs += 1

            if success_recs % 1000 == 0:
                print(f'Processed {success_recs} adds')

    print(f'Successfully added {success_recs} records')


def process_redo(engine):
    success_recs = 0

    print(f'\nStarting to process redo records...')

    try:
        while True:
            redo_record = bytearray()
            engine.processRedoRecord(redo_record)
            if not redo_record:
                break

            success_recs += 1
            if success_recs % 100 == 0:
                print(f'Processed {success_recs} redo records')
    except G2BadInputException as ex:
        mock_logger('ERROR', ex)
    except G2RetryableException as ex:
        mock_logger('WARN', ex)
    except (G2UnrecoverableException, G2Exception) as ex:
        mock_logger('CRITICAL', ex)
        raise

    print(f'Successfully processed {success_recs} redo records')


try:
    g2_engine = G2Engine()
    g2_engine.init('G2Engine', engine_config_json, False)
    add_records_from_file(g2_engine, '../../../Resources/Data/load-10K.json')
    redo_count = g2_engine.countRedoRecords()
    process_redo(g2_engine) if redo_count else print('No redo records to process')
    g2_engine.destroy()
except (G2BadInputException, G2RetryableException, G2UnrecoverableException, G2Exception) as ex:
    print(ex)
    sys.exit(-1)