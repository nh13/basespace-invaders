################################################################################
# Copyright 2017 Nils Homer
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

################################################################################
# This tool was adapted with permission from Mayank Tyagi <mtyagi@illumina.com>
################################################################################

import os, sys
from optparse import OptionParser, OptionGroup
from urllib2 import Request, urlopen, URLError
from BaseSpacePy.api.BaseSpaceAPI import BaseSpaceAPI
from BaseSpacePy.model.QueryParameters import QueryParameters as qp
import logging

class Runs:
    
    logging.basicConfig()

    @staticmethod
    def __get_files_to_download(myAPI, runId, fileLimit=1024):
        return myAPI.getRunFilesById(Id=runId, queryPars=qp({'Limit' : fileLimit}))

    @staticmethod
    def download(clientKey=None, clientSecret=None, accessToken=None, runId=None, runName=None, outputDirectory='\.', createBsDir=True):
        '''
        Downloads run-level files.

        Run Id and run name should not be specified together.

        All files for a given run will be downloaded based on either the unique run ID, or
        the first run found with matching experiment name.
                
        :param clientKey the Illumina developer app client key
        :param clientSecret the Illumina developer app client secret
        :param accessToken the Illumina developer app access token
        :param runId the BaseSpace run identifier
        :param runName the BaseSpace run experiment name
        :param outputDirectory the root output directory
        :param createBsDir true to recreate the path structure within BaseSpace, false otherwise
        '''
        appSessionId = ''
        apiServer = 'https://api.basespace.illumina.com/' # or 'https://api.cloud-hoth.illumina.com/'
        apiVersion = 'v1pre3'
        fileLimit = 1024
        runLimit = 100         

        # init the API
        if None != clientKey:
            myAPI = BaseSpaceAPI(clientKey, clientSecret, apiServer, apiVersion, appSessionId, accessToken)
        else:
            myAPI = BaseSpaceAPI(profile='DEFAULT')

        # get the current user
        user = myAPI.getUserById('current')

        expName = None
        if runId:
            run = myAPI.getRunById(Id=runId)
            runFiles = Runs.__get_files_to_download(myAPI, run.Id, fileLimit)
            expName = run.ExperimentName
        else:
            runs = myAPI.getAccessibleRunsByUser(qp({'Limit' : runLimit}))
            for run in runs:
                runId = run.Id
                if runName and runName == run.ExperimentName:
                    expName = run.ExperimentName
                    runFiles = Samples.__get_files_to_download(myAPI, runId)
                    if 0 < len(runFiles):
                        break
            if not expName:
                if runName:
                    print 'Could not find a run with name: %s' % runName
                else:
                    print 'Could not find a run for user'
                sys.exit(1)
        
        numFiles = len(runFiles)
        print "Will download files from %d ." % numFiles
        i = 0
        for runFile in runFiles:
            outDir = os.path.join(outputDirectory, expName)
            print 'Downloading (%d/%d): %s' % ((i+1), numFiles, str())
            print "BaseSpace File Path: %s" % runFile.Path
            print "Destination File Path: %s" % os.path.join(outDir, runFile.Name)
            if not options.dryRun:
                runFile.downloadFile(myAPI, outDir, createBsDir=createBsDir)
            i = i + 1
        print "Download complete."

if __name__ == '__main__':

    def check_option(parser, value, name):
        if None == value:
            print 'Option ' + name + ' required.\n'
            parser.print_help()
            sys.exit(1)
    
    parser = OptionParser()

    group = OptionGroup(parser, "Credential options")
    group.add_option('-K', '--client-key', help='the developer.basespace.illumina.com client key', dest='clientKey', default=None)
    group.add_option('-S', '--client-secret', help='the developer.basespace.illumina.com client token', dest='clientSecret', default=None)
    group.add_option('-A', '--access-token', help='the developer.basespace.illumina.com access token', dest='accessToken', default=None)
    parser.add_option_group(group)

    group = OptionGroup(parser, "Query options")
    group.add_option('-r', '--run-id', help='the run identifier (optional)', dest='runId', default=None)
    group.add_option('-R', '--run-name', help='the run experiment name (optional)', dest='runName', default=None)
    parser.add_option_group(group)
    
    group = OptionGroup(parser, "Miscellaneous options")
    group.add_option('-d', '--dry-run', help='dry run; do not download the files', dest='dryRun', action='store_true', default=False)
    group.add_option('-o', '--output-directory', help='the output directory', dest='outputDirectory', default='./')
    parser.add_option_group(group)
    
    if len(sys.argv[1:]) < 1:
        parser.print_help()
        sys.exit(1)

    options, args = parser.parse_args()
    if None != options.clientKey:
        #check_option(parser, options.clientKey, '-K')
        check_option(parser, options.clientSecret, '-S')
        check_option(parser, options.accessToken, '-A')
    if None == options.runId and None == options.runName:
        print 'One of the query options must be given.\n'
        parser.print_help()
        sys.exit(1)
    if None != options.runId and None != options.runName:
        print 'Both -p or -x may not be given together.\n'
        parser.print_help()
        sys.exit(1)

    Runs.download(options.clientKey, \
            options.clientSecret, \
            options.accessToken, \
            runId=options.runId, \
            runName=options.runName, \
            outputDirectory=options.outputDirectory)
