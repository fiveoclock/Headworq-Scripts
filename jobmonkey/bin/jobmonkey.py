#!/bin/python3
import os
import subprocess
import shutil
import argparse
import yaml
import requests
import re
import sys
from pprint import pprint
from systemd import journal

# global variables
config = None
debug_lvl = 0

def telegram_bot_sendtext(message):
  bot_token = cfg["global"]["notifications"]["telegram"]["bot_token"]
  chat_id = cfg["global"]["notifications"]["telegram"]["chat_id"]

  headers = {
    'Content-type': 'application/json',
    'Accept-Charset': 'UTF-8'
  }
  data = {
          'chat_id': chat_id,
          'text': message,
          'parse_mode': 'Markdown'
  }
  request_url = 'https://api.telegram.org/bot' + bot_token + '/sendMessage'

  response = requests.post(request_url, headers=headers, json=data)
  return response.json()


def list_jobs(jobs):
  from prettytable import PrettyTable
  table = PrettyTable(['Job name', 'Enabled'])
  table.align = "l"

  for job in cfg["jobs"]:
    job_name = job.get("name", None)

    if jobs:
      if (job_name in jobs) or re.match(jobs[0]+"$", job_name):
        pass
      else:
        continue

    table.add_row([job_name, job.get("enabled", True)] )

  print(table)


def debug(msg, level=1, end=None):
  if debug_lvl >= level: print(msg, end=end)


def process_jobs(jobs):
  for job in cfg["jobs"]:
    job_name = job.get("name")

    if (job_name in jobs) or re.match(jobs[0], job_name):
      pass
    else:
      continue

    # skip job if it isn't marked active
    if job.get("enabled", True) != True:
      debug("skipping job: '{}' - not enabled".format(job))
      continue

    debug("processing job: '{}'".format(job))

    error_count = 0
    report = ""
    # process all tasks of this job
    for task in job["tasks"]:
      debug("  running task: '{}' ...".format(task["run"]), level=2, end='')
      process = subprocess.run(task["run"].split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

      debug(" result '{}'".format( process.returncode ), level=2)
      debug(" detailed result '{}'".format( process ), level=3)

      # if process finished without errors and reporting is true
      if (process.returncode == 0) and task.get("report", False):
        report += "*Result from '{}':* '{}'\n\n".format(task["run"], str(process.stdout, 'utf-8').strip())

      # if process finished with errors
      if process.returncode != 0:
        error_count += 1
        report += "*Error: command failed:* '{}'\n\n".format(process)

    msg = "Job {} finished with {} error(s).\n\n{}".format(job_name, error_count, report)

    # send reports
    for report in job.get("reports", None):
      # retrieve report type and when condition
      report_type = report.get("type", None)
      when = report.get("when", "always")

      debug("  processing report '{}'".format( report_type ), level=1)

      # stop if 'when' condition is set to 'on-failure' and no errors occured
      if when == "on-failure" and error_count == 0: continue

      # go on if 'when' condition is set to 'always'
      if when == "always": pass

      # if report type is telegram
      if report.get("type", None) == "telegram":
        response = telegram_bot_sendtext(msg)
        debug("  response '{}'".format( response ), level=3)


def load_config(filename):
  global cfg
  debug("loading config file: '{}'".format(filename), level=2)
  with open(filename, "r") as cfgfile:
    cfg = yaml.load(cfgfile, Loader=yaml.CLoader)


def main(args):
  global debug_lvl
  # get verbose level - if not set default to 0
  debug_lvl = getattr(args, 'verbose', 0)

  debug("Arguments: '{}'".format(args), level=3)

  load_config(args.config)

  if args.command == "run":
    process_jobs(args.jobs)
  if args.command == "list":
    list_jobs(args.jobs)


if __name__ == "__main__":
  main_parser = argparse.ArgumentParser(description='Jobmonkey - runs jobs and sends reports')
  subparsers = main_parser.add_subparsers(title='valid actions', dest='command')

  # A list command
  list_parser = subparsers.add_parser('list', add_help=True, help='List jobs')
  list_parser.add_argument('jobs',
    action="store",
    nargs='*',
    help='the job(s) to list; enter one or more jobs; wildcards are allowed (default: all)')

  # A run command
  run_parser = subparsers.add_parser('run', add_help=True, help='Run one or more jobs')
  run_parser.add_argument('-d', '--dry-run',
    action="store_true",
    help='dont run the tasks')
  run_parser.add_argument('jobs',
    action="store",
    nargs='*',
    help='the job(s) to list; enter one or more jobs; wildcards are allowed (default: all)')


  # add arguments to both sub-parsers
  for p in [list_parser, run_parser]:
    p.add_argument('-c', '--config',
      action="store",
      help='the config file to use (default: /etc/jobmonkey/config.yml)',
      default='/etc/jobmonkey/config.yml')
    p.add_argument('-v',
      action="count",
      dest='verbose',
      default=0,
      help='be verbose (default: false)')

  # print help if no argument given
  if len(sys.argv)==1:
    main_parser.print_help(sys.stderr)
    sys.exit(1)

  args = main_parser.parse_args()
  main(args)
