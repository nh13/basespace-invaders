################################################################################
# Copyright 2016 Nils Homer
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
    def isBinaryContent(fn):
        for extension in ['pdf', 'bam', 'bai', 'png', 'vcf', 'gz']:
            if fn.endswith(extension):
                return True
        return False

    @staticmethod
    def upload(clientKey=None, clientSecret=None, accessToken=None, appResultId=None, fileNameRegexesInclude=list(), fileNameRegexesOmit=list(), inputDirectory='\.', dryRun=False, numRetries=3):
        '''
        Creates an App Result and uploads files.

        TODO
        Provide an App Result identifier, and optionally regexes to include or omit files 
        based on their names (path not included).  Omission takes precedence over inclusion.
                
        :param clientKey the Illumina developer app client key
        :param clientSecret the Illumina developer app client secret
        :param accessToken the Illumina developer app access token
        :param appResultId the BaseSpace App Result identifier
        :param fileNameRegexesInclude a list of regexes on which to include files based on name
        :param fileNameRegexesOmit a list of regexes on which to omit files based on name (takes precedence over include)
        :param inputDirectory the root input directory
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
            myAPI = BaseSpaceAPI(profile='DEFAULT', clientKey=clientKey, clientSecret=clientSecret, AccessToken=accessToken)

        # get the current user
        user = myAPI.getUserById('current')

        # get the app result
        appResult = myAPI.getAppResultById(Id=appResultId)
        appSession = appResult.AppSession
        print "Uploading files to the App Result: " + str(appResult)

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
        
        # walk the current directory structure
        for root, dirs, files in os.walk(inputDirectory):
            for fileName in files:
                localPath = os.path.join(root, fileName)
                directory = root.replace(inputDirectory, "") 
                if AppResults.isBinaryContent(fileName):
                    contentType = 'application/octet-stream'
                else:
                    contentType = 'text/plain'
                if keepFile(fileName):
                    print "Uploading file: %s" % localPath
                    if not options.dryRun:
                        retryIdx = 0
                        retryException = None
                        while retryIdx < numRetries:
                            try:
                                appResult.uploadFile(api=myAPI, localPath=localPath, fileName=fileName, directory=directory, contentType=contentType)
                            except BaseSpaceException.ServerResponseException as e:
                                retryIdx += 1
                                time.sleep(sleepTime)
                                retryException = e
                            else:
                                break
                        if retryIdx == numRetries:
                            raise retryException
        print "Upload complete"

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

    group = OptionGroup(parser, "Upload options")
    group.add_option('-z', '--input-directory', help='the input directory', dest='inputDirectory', default='./')
    group.add_option('-i', '--appresult-id', help='the AppResult identifier (required)', dest='appResultId', default=None)
    parser.add_option_group(group)
    
    group = OptionGroup(parser, "Miscellaneous options")
    group.add_option('-x', '--include-file-name-regex', help='include based on the file name based on the given regex (can be specified multiple times)', dest='fileNameRegexesInclude', default=list(), action='append')
    group.add_option('-X', '--omit-file-name-regex', help='omit based on the file name based on the given regex (can be specified multiple times). NB: has precedence over -x', dest='fileNameRegexesOmit', default=list(), action='append')
    group.add_option('-d', '--dry-run', help='dry run; do not download the files', dest='dryRun', action='store_true', default=False)
    #group.add_option('-f', '--force-overwrite', help='force overwrite if files are present', dest='force', action='store_true', default=False)
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

    AppResults.upload(options.clientKey, options.clientSecret, options.accessToken, \
            options.appResultId, \
            options.fileNameRegexesInclude, options.fileNameRegexesOmit, \
            inputDirectory=options.inputDirectory, dryRun=options.dryRun, numRetries=options.numRetries)
