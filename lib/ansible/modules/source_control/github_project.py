#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: my_sample_module

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''
try:
    import github
    HAS_GITHUB = True
except ImportError:
    HAS_GITHUB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def get_repo(owner, repository, owner_is_organization, connection):
    if owner_is_organization:
        o = connection.get_organization(owner)
    else:
        o = connection.get_user()
    try:
        return o.get_repo(repository)
    except github.GithubException as err:
        if err.status == 404:
            return None
        else:
            raise err


def create_repo(owner, repository, owner_is_organization, private, connection):
    if owner_is_organization:
        o = connection.get_organization(owner)
    else:
        o = connection.get_user()
    o.create_repo(repository, private=private)


def delete_repo():
    print("deleting repo")


def update_private_status():
    print("updating private status")


def run_module():
    # define available arguments/parameters a user can pass to the module

    module_args = {
        'owner': {'required': True},
        'repository': {'required': True},
        'user': {'required': True},
        'token': {'no_log': True},
        'password': {'no_log': True},
        'state': {'choices': ['present', 'absent'], 'default': 'present'},
        'private': {'type': 'bool'},
        'force': {'type': 'bool', 'default': False},
        'owner_is_organization': {'type': 'bool', 'default': False},
        'github_url': {'default': 'https://api.github.com'},
    }

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=(('password', 'token'),),
        required_one_of=(("password", "token"),),
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    if not HAS_GITHUB:
        module.fail_json(msg="PyGithub required for this module")

    try:
        github_conn = github.Github(
            module.params["user"],
            module.params.get("password") or module.params.get("token"),
            base_url=module.params["github_url"])

        repo = get_repo(module.params["owner"], module.params["repository"],
                        module.params["owner_is_organization"], github_conn)

        if repo is None and module.params["state"] == "present":
            create_repo(module.params["owner"], module.params["repository"], module.params["owner_is_organization"],
                        module.params["private"], github_conn)
            result["changed"] = True
        elif repo is not None and module.params["state"] == "absent":
            if module.params["force"]:
                delete_repo()
            else:
                module.fail_json(msg="Expected repository %s to be absent" % (module.params["repository"]))
            result["changed"] = True
        elif repo is not None and repo.private != module.params["private"]:
            update_private_status()
            result["changed"] = True

    except github.GithubException as err:
        module.fail_json(msg="Github error : %s" % (to_native(err)))

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()