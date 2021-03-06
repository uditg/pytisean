""" Wrapper to TISEAN files.
"""

import tempfile
import subprocess
import os, signal
from time import strftime
import numpy as np
from threading import Timer

__author__ = "Troels Bogeholm Mikkelsen"
__copyright__ = "Troels Bogeholm Mikkelsen 2016"
__credits__ = "Rainer Hegger, Holger Kantz and Thomas Schreiber"
__license__ = "MIT"
__version__ = "0.1"
__email__ = "bogeholm@nbi.ku.dk"
__status__ = "Development"

# Directory for temporary files
DIRSTR = '/tmp/'
# Prefix to identify these files
PREFIXSTR = 'pytisean_temp_'
# suffix - TISEAN likes .dat
SUFFIXSTR = '.dat'

# We will use the present time as a part of the temporary file name
def strnow():
    """ Return 'now' as a string with hyphenation
    """
    return strftime('%Y-%m-%d-%H-%M-%S')

def genfilename(ftype):
    """ Generate a file name.
    """
    return PREFIXSTR + strnow() + '_' + ftype + '_'

def gentmpfile(ftype):
    """ Generate temporary file and return file handle.
    """
    fhandle = tempfile.mkstemp(prefix=genfilename(ftype),
                               suffix=SUFFIXSTR,
                               dir=DIRSTR,
                               text=True)
    os.close(fhandle[0])
    return fhandle[1]

def tiseanio(command, *args, **kwargs): #data=None, silent=False):
    """ TISEAN input/output wrapper.

        Accept numpy array 'data' - run 'command' on this and return result.
        This function is meant as a wrapper around the TISEAN package.
    """
    # Return values if 'command' (or something else) fails
    res = None
    err_string = 'Something failed!'

    # If user specifies '-o' the save routine below will fail.
    if '-o' in args:
        raise ValueError('User is not allowed to specify an output file.')

    # Get Keyword Args
    data = kwargs.get('data', None)
    silent = kwargs.get('silent', False)

    # Names of temporary files
    fullname_in = gentmpfile('in')
    fullname_out = gentmpfile('out')

    # If no further args are specified, run this
    if not args:
        commandargs = [command, '-o', fullname_out]
    # Otherwise, we concatenate the args and command
    else:
        # User can specify float args - we convert
        arglist = [str(a) for a in args]
        commandargs = [command, fullname_in] + arglist + ['-o', fullname_out]

    kill = lambda process: process.kill()

    # We will clean up irregardless of following success.
    try:
    
        # Save the input to the temporary 'in' file
        # with open(fullname_in, mode='w') as fout:
        np.savetxt(fullname_in, data, delimiter='\t')
        
        # Here we call TISEAN (or something else?)
        subp = subprocess.Popen(commandargs,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                preexec_fn=os.setsid)
        (_, err_bytes) = subp.communicate()
        # my_timer = Timer(30, kill, [subp])
        # try:
        #    my_timer.start()
            # Communicate with the subprocess
        #    (_, err_bytes) = subp.communicate()
        # finally:
        #    my_timer.cancel()

        # Read the temporary 'out' file
        assert os.path.exists(fullname_out) and os.path.getsize(fullname_out) > 0, 'Output file not generated.'

        # with open(fullname_out, mode='w') as fin:
        res = np.loadtxt(fullname_out)#, delimiter='\t')

        # We will read this
        err_string = err_bytes.decode('utf-8')
    # Cleanup
    finally:
        # if subp.poll():
        #     subp.terminate()
        os.remove(fullname_in)
        os.remove(fullname_out)
        
    if not silent:
        print(err_string)

    # We assume that the user wants the (error) message as well.
    return res, err_string


def tiseano(command, *args, **kwargs):  # silent=False):
    """ TISEAN output wrapper.

        Run 'command' and return result.

        This function is meant as a wrapper around the TISEAN package.
    """
    # Return values if 'command' (or something else) fails
    res = None
    err_string = 'Something failed!'

    # Check for user specified args
    if '-o' in args:
        raise ValueError('User is not allowed to specify an output file.')

    # Get Keyword Args
    silent = kwargs.get('silent', False)

    # Handle to temporary file
    tf_out = gentmpfile()
    # Full names
    fullname_out = tf_out[1]

    # If no further args are specified, run this
    if not args:
        commandargs = [command, '-o', fullname_out]
    # Otherwise, we concatenate the args and command
    else:
        # User can specify float args - we convert
        arglist = [str(a) for a in args]
        commandargs = [command] + arglist + ['-o', fullname_out]

    # We will clean up irregardless of following success.
    try:
        # Here we call TISEAN (or something else?)
        subp = subprocess.Popen(commandargs,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=False)

        # Communicate with the subprocess
        (_, err_bytes) = subp.communicate()
        # Read the temporary 'out' file
        res = np.loadtxt(fullname_out)
        # We will read this
        err_string = err_bytes.decode('utf-8')

    # Cleanup
    finally:
        os.remove(fullname_out)

    if not silent:
        print(err_string)

    # We assume that the user wants the (error) message as well.
    return res, err_string
