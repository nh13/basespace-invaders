# BaseSpace Invaders

This contains a collection of scripts (one for now!) that I found useful to 
retrieve files from Illumina's BaseSpace.  Please run a script with no options 
to see its usage.

## Pre-requisites

### Python BaseSpace SDK
Please download and install the 
[python basespace sdk](http://github.com/basespace/basespace-python-sdk).

### Illumina's BaseSpace Developer Credentials

You will need proper credentials in order to communicate with Illumina's 
BaseSpace with these tools. Here are the steps to get one for your current 
BaseSpace account:

1. Go to https://developer.basespace.illumina.com/ and login.
2. Click on the "My Apps" link in the tool bar.
3. In the applications tab, click on the "Create New Application" button.
4. Fill out the Applications Details and then click the "Create Application" 
button.  Put dummy values if you encounter problems.
5. In the Credentials tab, you will need "Client Key", "Client Secret", and "
Access Token".

## Get sample files
The <code>samples2files.py</code> script downloads 
the sample-level files from BaseSpace.  The user can specify project Id, 
project name, sample Id, and sample Name.  Project Id and project name should 
not be specified together; similarly sample Id and sample name should not be 
specified together.   

1. If only a project Id or only a project name is given, all files for all
samples will be downloaded within that project.  If additionally a sample Id or 
sample name is given, then only the first matching sample within the project 
will be downloaded.
2. If only a sample Id is given, then all files for that sample will be downloaded.
3. If only a sample name is given, then all files within the first project 
containing a sample with matching name will be downloaded.
