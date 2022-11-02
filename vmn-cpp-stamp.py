#!/usr/bin/python3
import argparse
from version_stamp import vmn
from sys import stdout
import yaml
import subprocess

CMAKE_REQUIRED_GENERATOR = 'Unix Makefiles'


class CMakeConfigKeys:
    CMAKE_GENERATOR = 'CMAKE_GENERATOR:INTERNAL'
    CMAKE_BUILD_TYPE = 'CMAKE_BUILD_TYPE:STRING'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--target', required=True)
    parser.add_argument(
        "-r",
        "--release-mode",
        choices=["major", "minor", "patch", "hotfix", "micro"],
        default=None,
        help="major / minor / patch / hotfix",
        metavar="",
    )
    parser.add_argument(
        "--pr",
        "--prerelease",
        default=None,
        help="Prerelease version. Can be anything really until you decide "
        "to release the version",
    )

    return parser.parse_args()


def run_cmd(cmd):
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"failed to run: {' '.join(cmd)}.\n{e.output}\n{e.stderr}")


def valuable_config_line(l: str):
    return l and not l.startswith(tuple(['//', '#', '\n']))


def extrect_config_from_lines(lines_iter):
    lines = filter(valuable_config_line, lines_iter)
    key_value_list = map(lambda l: l.split('=', maxsplit=1), lines)

    # Strip all the spaces and convert into a dict
    config = dict(map(lambda kv: (kv[0].strip(), kv[1].strip('" \'\n\r')),
                      key_value_list))
    return config


def extract_config(file_path):
    # TODO: support better exception handling
    return extrect_config_from_lines(open(file_path).readlines())


def main():
    # TODO: add support for vmn debug
    # TODO: add support to gen only in dev mode
    args = parse_args()
    try:
        cmake_cache_config = extract_config(f'./CMakeCache.txt')

        if cmake_cache_config[CMakeConfigKeys.CMAKE_GENERATOR] != CMAKE_REQUIRED_GENERATOR:
            raise RuntimeError(
                f"please use '{CMAKE_REQUIRED_GENERATOR}' when creating your cmake build workspace")

        build_metadata = {}
        target_flags = extract_config(
            f'./CMakeFiles/{args.target}.dir/flags.make')

        target_link_flags = open(
            f'./CMakeFiles/{args.target}.dir/link.txt').readline().split(' ', maxsplit=1)[1].strip()

        # TODO: support windows
        distro_info = extract_config('/etc/lsb-release')
        build_metadata.update(target_flags)
        build_metadata['LINK_FLAGS'] = target_link_flags
        build_metadata['BUILD_TYPE'] = cmake_cache_config[CMakeConfigKeys.CMAKE_BUILD_TYPE]
        if build_metadata['BUILD_TYPE'] == '':
            raise RuntimeError('Error: your cmake project must have an explicit BUILD_TYPE')
        build_metadata['PLATFORM'] = distro_info['DISTRIB_DESCRIPTION']

        yaml.dump(build_metadata, open("build_metadata.yml", "w"))
        vmn_stamp = ['vmn', '--debug', 'stamp', args.target]
        if args.release_mode:
            vmn_stamp.extend(('-r', args.release_mode))
        if args.pr:
            vmn_stamp.extend(('--pr', args.pr))

        buildmetadata_name = f"{distro_info['DISTRIB_ID']}-{distro_info['DISTRIB_RELEASE']}"
        # run_cmd(vmn_stamp)

        stamped_version = None
        with vmn.VMNContextMAnager(vmn_stamp[1:]) as vmn_ctx:
            err = vmn.handle_stamp(vmn_ctx)
            if err:
                raise RuntimeError("vmn command failed")
            ver_info = vmn_ctx.vcs.backend.get_latest_reachable_version_info(
                args.target)
            stamped_version = ver_info['stamping']['app']['_version']

        run_cmd(
            ['vmn', '--debug', 'add', args.target, '--bm', buildmetadata_name, '--vmp', 'build_metadata.yml'])
        full_version = f"{stamped_version}+{buildmetadata_name}"
        run_cmd(['vmn', '--debug', 'gen', args.target, '-v',
                 full_version, '-t', '../ver_template_test.j2', '-o', 'out.cpp'])
    except Exception as e:
        if args.debug:
            raise
        print(f"error: {e}")
        exit(128)


if __name__ == "__main__":
    main()
