ansible_exec_ok
===============

Purpose
-------

This is the `exec_ok` ansible test plugin.

With it you can test whether a task has been successfully executed:

    - name: test something
      action: some action
      when: registered_variable is exec_ok

`exec_ok` exists to remedy ansible's built-in `success` plugin,
which will evaluate to `true` if a task was *not* executed.

The problem: why exec_ok exists
-------------------------------

This playbook:

    - hosts: machine
      tasks:
      # in our setup /foo/bar does __not__ exist!!!
      - name: check if /foo/bar exists
        stat: path=/foo/bar
        #                   # this task:
        failed_when:  False # * does not fail
        changed_when: False # * never changes anything
        register: foo_bar_status
    
      - name: register semantically expressive variable for foo_bar_status
        local_action: command "true"
        changed_when: False
        when: foo_bar_status.stat.exists
        register: baz_needs_to_be_run
      
      # this should not run, but it __does__!
      - name: run baz if /foo/bar exists
        command: run_baz
        when: baz_needs_to_be_run is success

... will probably not do what you expect!

In the first task the existence of `/foo/bar` will be checked. It
does not exist. So `foo_bar_status.stat.exists` will be `false`.

Subsequently we could use the condition `when: foo_bar_status.stat.exists`,
however that condition is a technical one and does not express the reason
_why_ we are checking ("the semantics").

So in order for our playbook to be semantically more expressive we register
the variable `baz_needs_to_be_run`.

Naively we could expect that if `foo_bar_status.stat.exists` then
`baz_needs_to_be_run is success` be true. And if `foo_bar_status` does _not_
exist, then `baz_needs_to_be_run is success` would not be true. However that
is __not__ the case.

The problem is that when the condition `when: foo_bar_status.stat.exists` is
not true, then the second task will be `skipped`.

The third task will now check whether `baz_needs_to_be_run is success` where
ansible [defines](https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/test/core.py#L44)
`success` as `not failed`.

The problem with this is that the second task *will* register the
`baz_needs_to_be_run` variable in order to be able to mark the variable,
which for ansible semantically refers to the _task_ being executed. But
ansible will __not__ set the variable to `failed` (since it was `skipped`).

And thus, since the third task checks for `baz_needs_to_be_run` being `success`
and `success` is defined as `not failed` and the `failed` property has __not__
been set in the second task, then `not failed` evaluates to `true` and thus
the condition `when: baz_needs_to_be_run is success` evaluates to true.

So even though the condition that determines whether `baz` should be
run (`when: foo_bar_status.stat.exists`) is false, ansible will run `baz`
nonetheless.

Installation
----------

I suggest to add to check out the plugin into your roles/ directory
as a submodule (provided that you keep the directory with your
ansible playbooks in a git repo):

    $ cd roles
    $ git submodule add https://github.com/sourcepole/ansible_exec_ok.git exec_ok

Then you'll need to make the test plugin available to ansible as a test plugin.
I suggest you symlink it into your `library`:

    $ cd library/test_plugins # create that directory in case it doesn't exist yet
    $ ln -s ../../roles/exec_ok/library/exec_ok.py

and tell ansible where to find the test plugin:

    $ cat ~/.ansible.cfg
    [...]
    test_plugins = /usr/share/ansible/plugins/test:/full/path/to/library/test_plugins

