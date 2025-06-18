# code-snippets-v3

## :warning: Warning

This repository is specifically for Senzing API V3.
It is not designed to work with Senzing SDK V4.

To find the Senzing API V4 version of this repository, visit [code-snippets-v4].

## Overview

Succinct examples of how you might use the Senzing APIs for operational tasks.

## Contents

1. [Legend]
1. [Warning]
1. [Senzing Engine Configuration]
1. [Senzing APIs Bare Metal Usage]
   1. [Configuration]
   2. [Usage]
1. [Docker Usage]
   1. [Configuration]
   2. [Usage]
1. [Items of Note]
   1. [With Info]
   2. [Parallel Processing]
   3. [Scalability]
   4. [Randomize Input Data]
   5. [Purging Senzing Repository Between Examples]
   6. [Input Load File Sizes]

### Legend

1. :thinking: - A "thinker" icon means that a little extra thinking may be required.
   Perhaps there are some choices to be made.
   Perhaps it's an optional step.
1. :pencil2: - A "pencil" icon means that the instructions may need modification before performing.
1. :warning: - A "warning" icon means that something tricky is happening, so pay attention.

## Warning

:warning::warning::warning: **Only run the code snippets against a test Senzing database instance.** Running the snippets adds and deletes data, and some snippets purge the entire database of currently ingested data. It is recommended to create a separate test Senzing project if you are using a bare metal Senzing install, or if using Docker a separate Senzing database to use only with the snippets. If you are getting started and are unsure please contact [Senzing Support]. :warning::warning::warning:

## Senzing Engine Configuration

A JSON configuration string is used by the snippets to specify initialization parameters to the Senzing engine:

```json
{
  "PIPELINE": {
    "SUPPORTPATH": "/home/senzing/mysenzproj1/data",
    "CONFIGPATH": "/home/senzing/mysenzproj1/etc",
    "RESOURCEPATH": "/home/senzing/mysenzproj1/resources"
  },
  "SQL": {
    "CONNECTION": "postgresql://user:password@host:5432:g2"
  }
}
```

The JSON configuration string is set via the environment variable `SENZING_ENGINE_CONFIGURATION_JSON`.

## Senzing APIs Bare Metal Usage

You may already have installed the Senzing APIs and created a Senzing project by following the [Quickstart Guide]. If not, and you would like to install the Senzing APIs directly on a machine, follow the steps in the [Quickstart Guide]. Be sure to review the API [Quickstart Roadmap], especially the [System Requirements].

### Configuration

When using a bare metal install, the initialization parameters used by the Senzing Python utilities are maintained within `<project_path>/etc/G2Module.ini`.

🤔To convert an existing Senzing project G2Module.ini file to a JSON string use one of the following methods:

- [G2ModuleIniToJson.py]

  - Modify the path to your projects G2Module.ini file.

- [jc]

  - ```console
    cat <project_path>/etc/G2Module.ini | jc --ini
    ```

- Python one liner

  - ```python
    python3 -c $'import configparser; ini_file_name = "<project_path>/etc/G2Module.ini";engine_config_json = {};cfgp = configparser.ConfigParser();cfgp.optionxform = str;cfgp.read(ini_file_name)\nfor section in cfgp.sections(): engine_config_json[section] = dict(cfgp.items(section))\nprint(engine_config_json)'
    ```

- [SenzingGo.py]

  - ```console
    <project_path>/python/SenzingGo.py --iniToJson
    ```

:pencil2: `<project_path>` in the above example should point to your project.

### Usage

1. Clone this repository
1. Export the engine configuration obtained for your project from [Configuration], e.g.,

```console
  export SENZING_ENGINE_CONFIGURATION_JSON='{"PIPELINE": {"SUPPORTPATH": "/<project_path>/data", "CONFIGPATH": "<project_path>/etc", "RESOURCEPATH": "<project_path>/resources"}, "SQL": {"CONNECTION": "postgresql://user:password@host:5432:g2"}}'
```

1. Source the Senzing project setupEnv file

```console
source <project_path>/setupEnv
```

1. Run code snippets

:pencil2: `<project_path>` in the above examples should point to your project.

## Docker Usage

The included Dockerfile leverages the [Senzing API runtime] image to provide an environment to run the code snippets.

### Configuration for Docker usage

When used with a container, the JSON configuration is relative to the paths within the container. The JSON configuration should look like:

```json
{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/g2/resources",
    "SUPPORTPATH": "/opt/senzing/data"
  },
  "SQL": {
    "CONNECTION": "postgresql://senzing:password@myhost:5432:g2"
  }
}
```

✏️You only need to modify the `CONNECTION` string to point to your Senzing database.

### Usage for Docker usage

1. Clone this repository
1. Export the engine configuration environment variable

```console
  export SENZING_ENGINE_CONFIGURATION_JSON='{"PIPELINE": {"CONFIGPATH": "/etc/opt/senzing", "RESOURCEPATH": "/opt/senzing/g2/resources", "SUPPORTPATH": "/opt/senzing/data"}, "SQL": {"CONNECTION": "postgresql://user:password@host:5432:g2"}}'
```

1. Build the Docker image

```console
cd <repository_dir>
docker build --tag senzing/code-snippets-v3 .
```

1. Run a container

```console
docker run \
  --env SENZING_ENGINE_CONFIGURATION_JSON \
  --interactive \
  --tty \
  --rm \
  senzing/code-snippets-v3
```

✏️You only need to modify the `CONNECTION` string to point to your Senzing database.

## Items of Note

### With Info

A feature of Senzing is the capability to pass changes from data manipulation API calls to downstream systems for analysis, consolidation and replication. Any API that can change the outcome of entity resolution have a "WithInfo" version of the API. For example, addRecord and addRecordWithInfo. The "WithInfo" version of the API returns a response message detailing any entities that were affected by the API. In the following example (from addRecordWithInfo) a single entity with the ID 7903 was affected.

```json
{
  "DATA_SOURCE": "TEST",
  "RECORD_ID": "10945",
  "AFFECTED_ENTITIES": [
    {
      "ENTITY_ID": 7903,
      "LENS_CODE": "DEFAULT"
    }
  ],
  "INTERESTING_ENTITIES": []
}
```

The AFFECTED_ENTITIES object contains a list of all entity IDs affected. Separate processes can query the affected entities and synchronize changes and information to downstream systems. For additional information see [Real-time replication and analytics].

### Parallel Processing

Many of the example tasks demonstrate concurrent execution with threads. The entity resolution process involves IO operations, the use of concurrent processes and threads when calling the Senzing APIs provides scalability and performance. If using multiple processes, each process should have its own instance of a Senzing engine, for example G2Engine. Each engine object can support multiple threads.

### Scalability

Many of the examples demonstrate using multiple threads to utilize the resources available on the machine. Consider loading data into Senzing and increasing the load rate, loading (and other tasks) can be horizontally scaled by utilizing additional machines.

If a single very large load file and 3 machines were available for performing data load, the file can be split into 3 with each machine running the sample code or your own application. Horizontal scaling such as this does require the Senzing database to have the capacity to accept the additional workload and not become the bottleneck.

### Randomize Input Data

When providing your own input file(s) to the snippets or your own applications and processing data manipulation tasks (adding, deleting, replacing), it is important to randomize the file(s) or other input methods when running multiple threads. If source records that pertain to the same entity are clustered together, multiple processes or threads could all be trying to work on the same entity concurrently. This causes contention and overhead resulting in slower performance. To prevent this contention always randomize input data.

You may be able to randomize your input files during ETL and mapping the source data to the [Senzing Entity Specification]. Otherwise utilities such as [shuf] or [terashuf] for large files can be used.

### Purging Senzing Repository Between Examples

When trying out different examples you may notice consecutive tasks complete much faster than an initial run. For example, running a loading task for the first time without the data in the system will be representative of load rate. If the same example is subsequently run again without purging the system it will complete much faster. This is because Senzing knows the records already exist in the system and it skips them.

To run the same example again and see representative performance, first [purge] the Senzing repository of the loaded data. Some examples don't require purging between running them, an example would be the deleting examples that require data to be ingested first. See the usage notes for each task category for an overview of how to use the snippets.

### Input Load File Sizes

There are different sized load files within the [Data] path that can be used to decrease or increase the volume of data loaded depending on the specification of your hardware. The files are named loadx.json, where the x specifies the number of records in the file.

[code-snippets-v4]: https://github.com/Senzing/code-snippets-v4
[Configuration]: #configuration
[Data]: Resources/Data/
[Docker Usage]: #docker-usage
[G2ModuleIniToJson.py]: Python/Tasks/Initialization/
[Input Load File Sizes]: #input-load-file-sizes
[Items of Note]: #items-of-note
[jc]: https://github.com/kellyjonbrazil/jc
[Legend]: #legend
[Parallel Processing]: #parallel-processing
[purge]: Python/Tasks/Initialization/PurgeRepository.py
[Purging Senzing Repository Between Examples]: #purging-senzing-repository-between-examples
[Quickstart Guide]: https://senzing.zendesk.com/hc/en-us/articles/115002408867-Quickstart-Guide
[Quickstart Roadmap]: https://senzing.zendesk.com/hc/en-us/articles/115001579954-API-Quickstart-Roadmap
[Randomize Input Data]: #randomize-input-data
[Real-time replication and analytics]: https://senzing.zendesk.com/hc/en-us/articles/4417768234131--Advanced-Real-time-replication-and-analytics
[Scalability]: #scalability
[Senzing API runtime]: https://github.com/Senzing/senzingapi-runtime
[Senzing APIs Bare Metal Usage]: #senzing-apis-bare-metal-usage
[Senzing Engine Configuration]: #senzing-engine-configuration
[Senzing Entity Specification]: https://senzing.zendesk.com/hc/en-us/articles/231925448-Generic-Entity-Specification
[Senzing Support]: https://senzing.zendesk.com/hc/en-us/requests/new
[SenzingGo.py]: https://github.com/Senzing/senzinggo
[shuf]: https://man7.org/linux/man-pages/man1/shuf.1.html
[System Requirements]: https://senzing.zendesk.com/hc/en-us/articles/115010259947
[terashuf]: https://github.com/alexandres/terashuf
[Usage]: #usage
[Warning]: #warning
[With Info]: #with-info
