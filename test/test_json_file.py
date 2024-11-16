#!/bin/python3

import json
import os
import shutil
import time
from dataclasses import dataclass
from threading import Thread
from unittest.mock import patch

import pytest
from assertpy import assert_that

from file_util.file_access_protector import json_safe_dump, json_safe_load

_temp_test_folder = "./test_data_json"
_test_file_path = "./test_data.json"
_data = {
    "web-app": {
        "servlet": [
            {
                "servlet-name": "cofaxCDS",
                "servlet-class": "org.cofax.cds.CDSServlet",
                "init-param": {
                    "configGlossary:installationAt": "Philadelphia, PA",
                    "configGlossary:adminEmail": "ksm@pobox.com",
                    "configGlossary:poweredBy": "Cofax",
                    "configGlossary:poweredByIcon": "/images/cofax.gif",
                    "configGlossary:staticPath": "/content/static",
                    "templateProcessorClass": "org.cofax.WysiwygTemplate",
                    "templateLoaderClass": "org.cofax.FilesTemplateLoader",
                    "templatePath": "templates",
                    "templateOverridePath": "",
                    "defaultListTemplate": "listTemplate.htm",
                    "defaultFileTemplate": "articleTemplate.htm",
                    "useJSP": False,
                    "jspListTemplate": "listTemplate.jsp",
                    "jspFileTemplate": "articleTemplate.jsp",
                    "cachePackageTagsTrack": 200,
                    "cachePackageTagsStore": 200,
                    "cachePackageTagsRefresh": 60,
                    "cacheTemplatesTrack": 100,
                    "cacheTemplatesStore": 50,
                    "cacheTemplatesRefresh": 15,
                    "cachePagesTrack": 200,
                    "cachePagesStore": 100,
                    "cachePagesRefresh": 10,
                    "cachePagesDirtyRead": 10,
                    "searchEngineListTemplate": "forSearchEnginesList.htm",
                    "searchEngineFileTemplate": "forSearchEngines.htm",
                    "searchEngineRobotsDb": "WEB-INF/robots.db",
                    "useDataStore": True,
                    "dataStoreClass": "org.cofax.SqlDataStore",
                    "redirectionClass": "org.cofax.SqlRedirection",
                    "dataStoreName": "cofax",
                    "dataStoreDriver": "com.microsoft.jdbc.sqlserver.SQLServerDriver",
                    "dataStoreUrl": "jdbc:microsoft:sqlserver://LOCALHOST:1433;DatabaseName=goon",
                    "dataStoreUser": "sa",
                    "dataStorePassword": "dataStoreTestQuery",
                    "dataStoreTestQuery": "SET NOCOUNT ON;select test='test';",
                    "dataStoreLogFile": "/usr/local/tomcat/logs/datastore.log",
                    "dataStoreInitConns": 10,
                    "dataStoreMaxConns": 100,
                    "dataStoreConnUsageLimit": 100,
                    "dataStoreLogLevel": "debug",
                    "maxUrlLength": 500
                }
            },
            {
                "servlet-name": "cofaxEmail",
                "servlet-class": "org.cofax.cds.EmailServlet",
                "init-param": {
                    "mailHost": "mail1",
                    "mailHostOverride": "mail2"
                }
            },
            {
                "servlet-name": "cofaxAdmin",
                "servlet-class": "org.cofax.cds.AdminServlet"
            },
            {
                "servlet-name": "fileServlet",
                "servlet-class": "org.cofax.cds.FileServlet"
            },
            {
                "servlet-name": "cofaxTools",
                "servlet-class": "org.cofax.cms.CofaxToolsServlet",
                "init-param": {
                    "templatePath": "toolstemplates/",
                    "log": 1,
                    "logLocation": "/usr/local/tomcat/logs/CofaxTools.log",
                    "logMaxSize": "",
                    "dataLog": 1,
                    "dataLogLocation": "/usr/local/tomcat/logs/dataLog.log",
                    "dataLogMaxSize": "",
                    "removePageCache": "/content/admin/remove?cache=pages&id=",
                    "removeTemplateCache": "/content/admin/remove?cache=templates&id=",
                    "fileTransferFolder": "/usr/local/tomcat/webapps/content/fileTransferFolder",
                    "lookInContext": 1,
                    "adminGroupID": 4,
                    "betaServer": True
                }
            }
        ]
    }
}


@dataclass
class Statistic:
    read_timeout_count = 0
    read_fail_count = 0
    write_timeout_count = 0
    write_fail_count = 0


def read_func(file_path: str, statistic: Statistic, run_time_s: float):
    stop_time = time.time() + run_time_s

    while time.time() <= stop_time:

        try:
            result = json_safe_load(file_path)
        except TimeoutError as e:
            print(f'[{time.time()}][read_func] timeout: {e}')
            statistic.read_timeout_count += 1
        except Exception as e:
            print(f'[{time.time()}][read func] exception: {e}')
            statistic.read_fail_count += 1

        time.sleep(0.01)


def write_func(file_path: str, data: dict, statistic: Statistic, run_time_s: float):
    stop_time = time.time() + run_time_s

    while time.time() <= stop_time:

        try:
            json_safe_dump(file_path, data)
        except TimeoutError as e:
            print(f'[{time.time()}][write_func] timeout: {e}')
            statistic.write_timeout_count += 1
        except Exception as e:
            print(f'[{time.time()}][write func] exception: {e}')
            statistic.write_fail_count += 1

        time.sleep(0.01)


@pytest.fixture(autouse=True, scope="module")
def prepare_test_data():
    if os.path.exists(_temp_test_folder):
        shutil.rmtree(_temp_test_folder)

    os.makedirs(_temp_test_folder)
    shutil.copy(_test_file_path, _temp_test_folder)

    yield

    shutil.rmtree(_temp_test_folder)


def test_concurrent_json_file_access():

    file_path = f'{_temp_test_folder}/{os.path.basename(_test_file_path)}'
    backup_file_path = f'{_temp_test_folder}/{os.path.basename(_test_file_path).replace(".json", "_backup.json")}'

    test_time = 5  # seconds

    read_thread1 = Thread(target=read_func, args=(
        file_path, Statistic, test_time), daemon=True)
    read_thread2 = Thread(target=read_func, args=(
        file_path, Statistic, test_time), daemon=True)
    write_thread1 = Thread(target=write_func, args=(
        file_path, _data, Statistic, test_time), daemon=True)
    write_thread2 = Thread(target=write_func, args=(
        file_path, _data, Statistic, test_time), daemon=True)

    read_thread1.start()
    write_thread1.start()
    read_thread2.start()
    write_thread2.start()

    read_thread1.join()
    write_thread1.join()
    read_thread2.join()
    write_thread2.join()

    assert_that(Statistic.read_timeout_count).is_equal_to(0)
    assert_that(Statistic.read_fail_count).is_equal_to(0)
    assert_that(Statistic.write_timeout_count).is_equal_to(0)
    assert_that(Statistic.write_fail_count).is_equal_to(0)

    assert_that(os.path.exists(backup_file_path))

    with open(backup_file_path, 'r') as f:
        backup_content = json.load(f)

    assert_that(backup_content).is_equal_to(_data)


@patch('subprocess.call', return_value=1)
def test_get_file_lock_timeout(mock_subprocess_call):
    file_path = f'{_temp_test_folder}/{os.path.basename(_test_file_path)}'

    with pytest.raises(TimeoutError):
        r = json_safe_load(file_path)


def test_load_file_not_exist():
    file_path = f'{_temp_test_folder}/abc.json'

    with pytest.raises(AttributeError):
        r = json_safe_load(file_path)


def test_dump_file_with_wrong_data():
    file_path = f'{_temp_test_folder}/{os.path.basename(_test_file_path)}'

    with pytest.raises(AttributeError):
        json_safe_dump(file_path, "")


def test_wrong_file_extension():
    file_path = f'{_temp_test_folder}/abc.yaml'

    with pytest.raises(AttributeError):
        json_safe_dump(file_path, {})


def test_write_new_file():
    file_path = f'{_temp_test_folder}/new.json'
    backup_file_path = f'{_temp_test_folder}/new_backup.json'

    json_safe_dump(file_path, {})

    assert_that(os.path.exists(file_path))
    assert_that(os.path.exists(backup_file_path))


@patch('json.load', return_value="")
def test_file_and_backup_corruption_in_load(mock_json_load):
    file_path = f'{_temp_test_folder}/{os.path.basename(_test_file_path)}'

    with pytest.raises(ValueError):
        r = json_safe_load(file_path)


@patch('json.load', return_value="")
def test_file_corruption_in_dump(mock_json_load):
    file_path = f'{_temp_test_folder}/{os.path.basename(_test_file_path)}'

    with pytest.raises(ValueError):
        json_safe_dump(file_path, {})


@patch('json.load', return_value="")
def test_file_corruption_and_backup_not_exist_in_load(mock_json_load):
    file_path = f'{_temp_test_folder}/{os.path.basename(_test_file_path)}'
    backup_file_path = f'{_temp_test_folder}/{os.path.basename(_test_file_path).replace(".json", "_backup.json")}'

    if os.path.exists(backup_file_path):
        os.remove(backup_file_path)

    with pytest.raises(ValueError):
        r = json_safe_load(file_path)
