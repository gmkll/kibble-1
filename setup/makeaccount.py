#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, os, os.path
import elasticsearch
import argparse
import yaml
import bcrypt

import sys
sys.path.append('../')

import api.plugins.database

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-u", "--username", required=True, help="Username (email) of accoun to create")
arg_parser.add_argument("-p", "--password", required=True, help="Password to set for account")
arg_parser.add_argument("-n", "--name", help="Real name (displayname) of account (optional)")
arg_parser.add_argument("-A", "--admin", action="store_true", help="Make account global admin")
arg_parser.add_argument("-a", "--orgadmin", action="store_true", help="Make account owner of orgs invited to")
arg_parser.add_argument("-o", "--org", help="Invite to this organisation (id)")

args = arg_parser.parse_args()

# Load Kibble master configuration
config = yaml.load(open("../api/yaml/kibble.yaml"), Loader=yaml.Loader)

# use es 7 mapping if
DB = api.plugins.database.KibbleDatabase(config)

username = args.username
password = args.password
name = args.name if args.name else args.username
admin = True if args.admin else False
adminorg = True if args.orgadmin else False
orgs = [args.org] if args.org else []
aorgs = orgs if adminorg else []

salt = bcrypt.gensalt()
pwd = bcrypt.hashpw(password.encode('utf-8'), salt)  #.decode('ascii')

doc = {
        'email': username,                          # Username (email)
        'password': pwd,                            # Hashed password
        'displayName': username,                    # Display Name
        'organisations': orgs,                        # Orgs user belongs to (default is none)
        'ownerships': aorgs,                           # Orgs user owns (default is none)
        'defaultOrganisation': None,                # Default org for user
        'verified': True,                           # Account verified via email?
        'userlevel': "admin" if admin else "user"   # User level (user/admin)
    }

# doc_type is adpated for es > 6
res = DB.ES.index(index=DB.dbname, doc_type='useraccount', id = username, body = doc) # 

print("Account '%s' %s in index %s!" %( username, res['result'],  DB.dbname) )

