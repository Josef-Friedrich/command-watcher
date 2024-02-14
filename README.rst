.. image:: http://img.shields.io/pypi/v/command-watcher.svg
    :target: https://pypi.org/project/command-watcher
    :alt: This package on the Python Package Index

.. image:: https://github.com/Josef-Friedrich/command-watcher/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/Josef-Friedrich/command-watcher/actions/workflows/tests.yml
    :alt: Tests

command_watcher
===============

Module to watch the execution of shell scripts. Both streams (`stdout`
and `stderr`) are captured.

.. code:: python

    watch = Watch()
    watch.log.critical('msg')
    watch.log.error('msg')
    watch.log.warning('msg')
    watch.log.info('msg')
    watch.log.debug('msg')
    watch.run(['rsync', '-av', '/home', '/backup'])

.. code-block:: python

    from command_watcher import Watch
    watch = Watch(
        config_file='/etc/command-watcher.ini',
        service_name='texlive_update'
    )

    tlmgr = '/usr/local/texlive/bin/x86_64-linux/tlmgr'

    watch.run('{} update --self'.format(tlmgr))
    watch.run('{} update --all'.format(tlmgr))
    installed_packages = watch.run(
        '{} info --only-installed'.format(tlmgr), log=False
    )
    all_packages = watch.run('{} info'.format(tlmgr), log=False)

    watch.final_report(
        status=0,
        performance_data={
            'installed_packages': installed_packages.line_count_stdout,
            'all_packages': all_packages.line_count_stdout,
        },
    )

.. code-block:: ini

    [email]
    subject_prefix = [cwatcher]
    from_addr =
    to_addr = logs@example.com
    to_addr_critical = critical@example.com
    smtp_login = mailer
    smtp_password = 1234
    smtp_server = mail.example.com:587

    [nsca]
    remote_host = 1.2.3.4
    password = asdf1234
    encryption_method = 8
    ; port = 5667

    [icinga]
    url = https://icinga.example.com:5665
    user = user
    password = 1234

    [beep]
    activated = True
