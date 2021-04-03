# JobMonkey
Just a small script for running jobs and sending reports.

The configuration is stored in a yaml file. Jobs consist of one mor more tasks. Where each task is a command to be executed. 

Features:

* Configuration is stored in a yaml file.
* Jobs can be disabled
* Job based reporting can be enabled 'always' or 'on-failure'
* Reporting can be enabled for single tasks
* Reports are sent via Telegram


The script can send reports which can be defined on a task or job level. 

    # jobmonkey -h
    usage: jobmonkey [-h] {list,run} ...

    Jobmonkey - runs jobs and sends reports

    optional arguments:
      -h, --help  show this help message and exit

    valid actions:
      {list,run}
        list      List jobs
        run       Run one or more jobs
        


The config yaml looks like this:

    # cat /etc/jobmonkey/config.yml
    
    global:
      user: root
      notifications:
        telegram:
          bot_token: 'XXXXXXXXXX:XXX_XXXXXXXXXX_XXXXXXXXXXXXXXXXXXXX'
          chat_id: '0000000000'

    jobs:
      - name: test
        enabled: false
        reports:
          - type: telegram
            when: on-failue
        tasks:
          - run: "hostname -f"
            report: true
          - run: "false"
            report: false

      - name: upgrade-check
        descr: "Check for security updates"
        enabled: true
        reports:
          - type: telegram
            when: always
        tasks:
          - run: "apt update"
          - run: "/usr/local/sbin/print_updates.py"
            report: true
