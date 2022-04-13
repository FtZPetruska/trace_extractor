# Trace Extractor

A wrapper around ffprobe that takes MPEG-4 files and outputs video traces in a format readable by [ns-3](https://gitlab.com/nsnam/ns-3-dev)'s UdpTraceClient application.

## Dependencies

You need to have [ffmpeg](https://ffmpeg.org/)'s `ffprobe` present in your `PATH`. Alternatively, you can use a custom `ffprobe` with the `--ffprobe-path` argument:

```
python3 -m trace_extractor --ffprobe-path /path/to/ffprobe
```

## Installation

`trace_extractor` can be installed via `pip`:

```
pip install trace-extractor
```

## Usage

Running the command without arguments will scan the `input` folder in the current directory for mp4 files, process each of them and write the results in an `output` folder in the current directory.

```
python3 -m trace_extractor
```

Input files can also be manually specified as positional arguments, note that the `input` folder will be scanned regardless.

```
python3 -m trace_extractor file1.mp4 file2.mp4 ...
```

## Example

An example video is present in the input folder, it is a recording of id Software's 1993 DOOM's DEMO1 demo played back on the [prboom-plus](https://github.com/coelckers/prboom-plus) source port.
