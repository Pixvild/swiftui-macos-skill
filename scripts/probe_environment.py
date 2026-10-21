#!/usr/bin/env python3
"""Read toolchain identity; does not build, alter Xcode settings, or infer a target."""
from __future__ import annotations
import argparse
import json
import platform
import shutil
import subprocess
from pathlib import Path
from doclib import utc_now, write_json


def run_command(command):
    if shutil.which(command[0]) is None:
        return {'status':'unavailable','command':command,'exit_code':None,'output':None}
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=20)
        return {'status':'ok' if result.returncode==0 else 'failed','command':command,
                'exit_code':result.returncode,'output':(result.stdout+result.stderr).strip()}
    except (OSError,subprocess.TimeoutExpired) as error:
        return {'status':'failed','command':command,'exit_code':None,'output':str(error)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Optional JSON report; otherwise print only')
    args=parser.parse_args()
    is_mac=platform.system()=='Darwin'
    report={'checked_at':utc_now(),'host_os':platform.system(),'host_architecture':platform.machine(),
            'macos_validation_possible':is_mac,'deployment_targets':'not_inspected',
            'swift_language_mode':'not_inspected','strict_concurrency':'not_inspected',
            'default_actor_isolation':'not_inspected','project_build':'not_run','runtime_tests':'not_run'}
    if is_mac:
        commands=[['sw_vers'],['xcode-select','-p'],['xcodebuild','-version'],
                  ['xcrun','--sdk','macosx','--show-sdk-version'],['xcrun','--sdk','macosx','--show-sdk-path'],
                  ['xcrun','swift','--version']]
    else:
        commands=[['swift','--version']]
        report['limitation']='A Swift executable on a non-macOS host does not provide macOS SwiftUI/AppKit verification.'
    report['commands']=[run_command(command) for command in commands]
    if args.output: write_json(args.output,report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
