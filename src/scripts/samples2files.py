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

import os, sys
from optparse import OptionParser, OptionGroup
from urllib2 import Request, urlopen, URLError
from BaseSpacePy.api.BaseSpaceAPI import BaseSpaceAPI
from BaseSpacePy.model.QueryParameters import QueryParameters as qp
import logging

class Samples:
    
    logging.basicConfig()

    @staticmethod
    def __get_files_to_download(myAPI, projectId, sampleId, sampleName, sampleLimit=1024, sampleFileLmit=1024):
        sampleToFiles = {}
        samples = myAPI.getSamplesByProject(Id=projectId, queryPars=qp({'Limit' : sampleLimit}))
        for sample in samples:
            if None != sampleId and sampleId != sample.Id:
                continue
            elif None != sampleName and sampleName != sample.Name:
                continue
            sampleFiles = myAPI.getSampleFilesById(Id=sample.Id, queryPars=qp({'Limit' : sampleFileLmit}))
            sampleToFiles[sample.Id] = sampleFiles
        return sampleToFiles

    @staticmethod
    def download(clientKey=None, clientSecret=None, accessToken=None, sampleId=None, projectId=None, sampleName=None, projectName=None, outputDirectory='\.', createBsDir=True):
        '''
        Downloads sample-level files.

        Project Id and project name should
        not be specified together; similarly sample Id and sample name should not be
        specified together.

        1. If only a project Id or only a project name is given, all files for all
        samples will be downloaded within that project.  If additionally a sample Id or
        sample name is given, then only the first matching sample within the project
        will be downloaded.
        2. If only a sample Id is given, then all files for that sample will be downloaded.
        3. If only a sample name is given, then all files within the first project
        containing a sample with matching name will be downloaded.
                
        :param clientKey the Illumina developer app client key
        :param clientSecret the Illumina developer app client secret
        :param accessToken the Illumina developer app access token
        :param sampleId the BaseSpace sample identifier
        :param projectId the BaseSpace project identifier
        :param sampleName the BaseSpace sample name
        :param projectName the BaseSpace project name
        :param outputDirectory the root output directory
        :param createBsDir true to recreate the path structure within BaseSpace, false otherwise
        '''
        appSessionId = ''
        apiServer = 'https://api.basespace.illumina.com/' # or 'https://api.cloud-hoth.illumina.com/'
        apiVersion = 'v1pre3'
        projectLimit = 1024
        sampleLimit = 1024         
        sampleFileLimit = 1024 

        # init the API
        if None != clientKey:
            myAPI = BaseSpaceAPI(clientKey, clientSecret, apiServer, apiVersion, appSessionId, accessToken)
        else:
            myAPI = BaseSpaceAPI(profile='DEFAULT')

        # get the current user
        user = myAPI.getUserById('current')

        sampleToFiles = {}
        if None != projectId:
            sampleToFiles = Samples.__get_files_to_download(myAPI, projectId, sampleId, sampleName, sampleLimit, sampleFileLimit)
        else:
            offset = 0
            while True:
                myProjects = myAPI.getProjectByUser(qp({'Limit' : projectLimit, 'Offset' : offset}))
                if len(myProjects) == 0:
                    break
                for project in myProjects:
                    projectId = project.Id
                    sys.stderr.write("project.Name: " + str(project.Name)  + " projectName: " + str(projectName) + '\n')
                    if None != projectName and project.Name != projectName:
                        continue
                    sampleToFiles = Samples.__get_files_to_download(myAPI, projectId, sampleId, sampleName, sampleLimit, sampleFileLimit)
                    if 0 < len(sampleToFiles):
                        break
                if 0 < len(sampleToFiles):
                    break
                offset += projectLimit
        numFiles = sum([len(sampleToFiles[sampleId]) for sampleId in sampleToFiles])
        print "Will download files from %d ." % numFiles
        i = 0
        for sampleId in sampleToFiles:
            for sampleFile in sampleToFiles[sampleId]:
                print 'Downloading (%d/%d): %s' % ((i+1), numFiles, str(sampleFile))
                print "BaseSpace File Path: %s" % sampleFile.Path
                print "Sample Id: %s" % sampleId
                if not options.dryRun:
                    if createBsDir:
                        sampleOutputDirectory = os.path.join(outputDirectory, sampleId)
                    else:
                        sampleOutputDirectory = outputDirectory
                    sampleFile.downloadFile(myAPI, sampleOutputDirectory, createBsDir=createBsDir)
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
    group.add_option('-s', '--sample-id', help='the sample identifier (optional)', dest='sampleId', default=None)
    group.add_option('-x', '--sample-name', help='the sample name (optional)', dest='sampleName', default=None)
    group.add_option('-p', '--project-id', help='the project identifier (optional)', dest='projectId', default=None)
    group.add_option('-y', '--project-name', help='the project name (optional)', dest='projectName', default=None)
    parser.add_option_group(group)
    
    group = OptionGroup(parser, "Miscellaneous options")
    group.add_option('-d', '--dry-run', help='dry run; do not download the files', dest='dryRun', action='store_true', default=False)
    group.add_option('-o', '--output-directory', help='the output directory', dest='outputDirectory', default='./')
    group.add_option('-b', '--create-basespace-directory-structure', help='recreate the basespace directory structure in the output directory', \
            dest='createBsDir', action='store_false', default=True)
    parser.add_option_group(group)
    
    if len(sys.argv[1:]) < 1:
        parser.print_help()
        sys.exit(1)

    options, args = parser.parse_args()
    if None != options.clientKey:
        #check_option(parser, options.clientKey, '-K')
        check_option(parser, options.clientSecret, '-S')
        check_option(parser, options.accessToken, '-A')
    if None == options.projectId and None == options.sampleId and None == options.projectName and None == options.sampleName:
        print 'One of the query options must be given.\n'
        parser.print_help()
        sys.exit(1)
    if None != options.sampleId and None != options.sampleName:
        print 'Both -s or -y may not be given together.\n'
        parser.print_help()
        sys.exit(1)
    if None != options.projectId and None != options.projectName:
        print 'Both -p or -x may not be given together.\n'
        parser.print_help()
        sys.exit(1)

    Samples.download(options.clientKey, options.clientSecret, options.accessToken, \
            sampleId=options.sampleId, projectId=options.projectId, \
            sampleName=options.sampleName, projectName=options.projectName, \
            outputDirectory=options.outputDirectory, createBsDir=options.createBsDir)
