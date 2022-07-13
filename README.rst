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
