################################################################################
# Copyright 2014 Nils Homer
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

import os, sys, re
from optparse import OptionParser, OptionGroup
from urllib2 import Request, urlopen, URLError
from BaseSpacePy.api.BaseSpaceAPI import BaseSpaceAPI
from BaseSpacePy.model.QueryParameters import QueryParameters as qp
from BaseSpacePy.api import BaseSpaceException
import logging
import time

class AppResults:
    
    logging.basicConfig()

    @staticmethod
    def download(clientKey=None, clientSecret=None, accessToken=None, appResultId=None, fileNameRegexesInclude=list(), fileNameRegexesOmit=list(), outputDirectory='\.', createBsDir=True, force=False, numRetries=3):
        '''
        Downloads App Result files.

        Provide an App Result identifier, and optionally regexes to include or omit files 
        based on their names (path not included).  Omission takes precedence over inclusion.
                
        :param clientKey the Illumina developer app client key
        :param clientSecret the Illumina developer app client secret
        :param accessToken the Illumina developer app access token
        :param appResultId the BaseSpace App Result identifier
        :param fileNameRegexesInclude a list of regexes on which to include files based on name
        :param fileNameRegexesOmit a list of regexes on which to omit files based on name (takes precedence over include)
        :param outputDirectory the root output directory
        :param createBsDir true to recreate the path structure within BaseSpace, false otherwise
        :param force use the force: overwrite existing files if true, false otherwise
        :param numRetries the number of retries for a single download API call
        '''
        appSessionId = ''
        apiServer = 'https://api.basespace.illumina.com/' # or 'https://api.cloud-hoth.illumina.com/'
        apiVersion = 'v1pre3'
        fileLimit = 10000
        sleepTime = 1.0

        # init the API
        if None != clientKey:
            myAPI = BaseSpaceAPI(clientKey, clientSecret, apiServer, apiVersion, appSessionId, accessToken)
        else:
            myAPI = BaseSpaceAPI(profile='DEFAULT')

        # get the current user
        user = myAPI.getUserById('current')

        appResult = myAPI.getAppResultById(Id=appResultId)
        print "Retrieving files from the App Result: " + str(appResult)

        # Get all the files from the AppResult
        filesToDownload = appResult.getFiles(myAPI, queryPars=qp({'Limit' : fileLimit}))

        # Filter file names based on the include or omit regexes
        includePatterns = [re.compile(pattern) for pattern in fileNameRegexesInclude]
        omitPatterns = [re.compile(pattern) for pattern in fileNameRegexesOmit]
        def includePatternMatch(f):
            if not includePatterns:
                return True
            for pattern in includePatterns:
                if pattern.match(f):
                    return True
            return False
        def omitPatternMatch(f):
            if not omitPatterns:
                return False
            for pattern in omitPatterns:
                if pattern.match(f):
                    return True
            return False
        def keepFile(f): 
            return includePatternMatch(f) and not omitPatternMatch(f)
        filesToDownload = [f for f in filesToDownload if keepFile(str(f))]

        print "Will download %d files." % len(filesToDownload)
        for i in range(len(filesToDownload)):
            appResultFile = filesToDownload[i]
            print 'Downloading (%d/%d): %s' % ((i+1), len(filesToDownload), str(appResultFile))
            print "File Path: %s" % appResultFile.Path
            if not options.dryRun:
                outputPath = str(appResultFile.Path) 
                if not createBsDir:
                    outputPath = os.path.basename(outputPath)
                if os.path.exists(outputPath):
                    if force:
                        print "Overwritting: %s" % outputPath
                    else:
                        print "Skipping existing file: %s" % outputPath
                        continue
                else:
                    print "Downloading to: %s" % outputPath
                retryIdx = 0
                retryException = None
                while retryIdx < numRetries:
                    try:
                        appResultFile.downloadFile(myAPI, outputDirectory, createBsDir=createBsDir)
                    except BaseSpaceException.ServerResponseException as e:
                        retryIdx += 1
                        time.sleep(sleepTime)
                        retryException = e
                    else:
                        break
                if retryIdx == numRetries:
                    raise retryException
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
    group.add_option('-i', '--appresult-id', help='the AppResult identifier (required)', dest='appResultId', default=None)
    group.add_option('-x', '--include-file-name-regex', help='include based on the file name based on the given regex (can be specified multiple times)', dest='fileNameRegexesInclude', default=list(), action='append')
    group.add_option('-X', '--omit-file-name-regex', help='omit based on the file name based on the given regex (can be specified multiple times). NB: has precedence over -x', dest='fileNameRegexesOmit', default=list(), action='append')
    parser.add_option_group(group)
    
    group = OptionGroup(parser, "Miscellaneous options")
    group.add_option('-d', '--dry-run', help='dry run; do not download the files', dest='dryRun', action='store_true', default=False)
    group.add_option('-o', '--output-directory', help='the output directory', dest='outputDirectory', default='./')
    group.add_option('-b', '--create-basespace-directory-structure', help='recreate the basespace directory structure in the output directory', \
            dest='createBsDir', action='store_false', default=True)
    group.add_option('-f', '--force-overwrite', help='force overwrite if files are present', dest='force', action='store_true', default=False)
    group.add_option('-n', '--num-retries', help='the number of retries for a download API call', dest='numRetries', default=3)
    parser.add_option_group(group)
    
    options, args = parser.parse_args()
    if None != options.clientKey:
        check_option(parser, options.clientKey, '-K')
        check_option(parser, options.clientSecret, '-S')
        check_option(parser, options.accessToken, '-A')
    if None == options.appResultId:
        print 'The App Result identifier (-i) option must be given.\n'
        parser.print_help()
        sys.exit(1)

    AppResults.download(options.clientKey, options.clientSecret, options.accessToken, \
            options.appResultId, options.fileNameRegexesInclude, options.fileNameRegexesOmit, \
            outputDirectory=options.outputDirectory, createBsDir=options.createBsDir, \
            force=options.force, numRetries=options.numRetries)
