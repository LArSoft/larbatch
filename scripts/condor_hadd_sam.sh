#! /bin/bash
#------------------------------------------------------------------
#
# Purpose: A batch script to fetch root files from sam and combine
#          them using hadd.
#
# Adapted from condor_lBdetMC.sh by E. Church.
#
# Usage:
#
# condor_hadd_sam.sh [options]
#
# Options:
#
# -c, --config            - For compatibility (ignored).
# -T, --TFileName  <arg>  - TFile output file name
# --nfile <arg>           - Number of files to process per worker.
#
# Sam and parallel project options.
#
# --sam_user <arg>        - Specify sam user (default $GRID_USER).
# --sam_group <arg>       - Specify sam group (default --group option).
# --sam_station <arg>     - Specify sam station (default --group option).
# --sam_defname <arg>     - Sam dataset definition name.
# --sam_project <arg>     - Sam project name.
# --sam_start             - Specify that this worker should be responsible for
#                           starting and stopping the sam project.
# --recur                 - Recursive input dataset (force snapshot).
# --sam_schema <arg>      - Use this option with argument "root" to stream files using
# --os <arg>              - A copy of the os argument passed to jobsub.  May be used
#                           to affect definition of UPS_OVERRIDE.
# --data_file_type        - Specify data file type (default "root," repeatable).
#
# Larsoft options.
#
# --ups <arg>             - Comma-separated list of top level run-time ups products.
# -r, --release <arg>     - Release tag.
# -q, -b, --build <arg>   - Release build qualifier (default "debug", or "prof").
# --localdir <arg>        - Larsoft local test release directory (default none).
# --localtar <arg>        - Tarball of local test release.
# --mrb                   - Ignored (for compatibility).
# --srt                   - Exit with error status (SRT run time no longer supported).
#
# Other options.
#
# -h, --help              - Print help.
# -i, --interactive       - For interactive use.
# -g, --grid              - Be grid-friendly.
# --group <arg>           - Group or experiment (required).
# --workdir <arg>         - Work directory (required).
# --outdir <arg>          - Output directory (required).
# --logdir <arg>          - Log directory (required).
# --scratch <arg>         - Scratch directory (only for interactive).
# --cluster <arg>         - Job cluster (override $CLUSTER)
# --process <arg>         - Process within cluster (override $PROCESS).
# --procmap <arg>         - Name of process map file (override $PROCESS).
# --init-script <arg>     - User initialization script execute.
# --init-source <arg>     - User initialization script to source (bash).
# --end-script <arg>      - User end-of-job script to execute.
# --init <path>           - Absolute path of environment initialization script.
#
# End options.
#
# Run time environment setup.
#
# MRB run-time environmental setup is controlled by four options:
#  --release (-r), --build (-b, -q), --localdir, and --localtar.  
#
# a) Use option --release or -r to specify version of top-level product(s).  
# b) Use option --build or -b to specify build full qualifiers (e.g. 
#    "debug:e5" or "e5:prof").
# c) Options --localdir or --localtar are used to specify your local
#    test release.  Use one or the other (not both).
#
#    Use --localdir to specify the location of your local install
#    directory ($MRB_INSTALL).
#
#    Use --localtar to specify thye location of a tarball of your
#    install directory (made relative to $MRB_INSTALL).
#
#    Note that --localdir is not grid-friendly.
#
# Notes.
#
# 1.  Each batch worker is uniquely identified by two numbers stored
#     in environment variables $CLUSTER and $PROCESS (the latter is 
#     a small integer that starts from zero and varies for different
#     jobs in a parallel job group).  These environment variables are
#     normally set by the batch system, but can be overridden by options 
#     --cluster, --process, and --procmap (e.g. to rerun failed jobs).
#
# 2.  The work directory must be set to an existing directory owned
#     by the submitter and readable by the batch worker.  Files from the 
#     work directory are copied to the batch worker scratch directory at
#     the start of the job.
#
# 3.  The initialization and end-of-job
#     scripts (optins --init-script, --init-source, --end-script) may
#     be stored in the work directory specified by option --workdir, or they
#     may be specified as absolute paths visible on the worker node.
#
# 4.  A local test release may be specified as an absolute path using
#     --localdir, or a tarball using --localtar.  The location of the tarball
#     may be specified as an absolute path visible on the worker, or a 
#     relative path relative to the work directory.
#
# 5.  The output directory must exist and be writable by the batch
#     worker (i.e. be group-writable for grid jobs).  The worker
#     makes a new subdirectory called ${CLUSTER}_${PROCESS} in the output
#     directory and copies all files in the batch scratch directory there 
#     at the end of the job.  If the output directory is not specified, the
#     default is /grid/data/<group>/outstage/<user> (user is defined as 
#     owner of work directory).
#
# 6.  This script reads input files from sam using the standard sam project api.
#     All files are fetched from sam, then then are combined by a single 
#     invocation of hadd.  This way of working implies an upper limit on
#     the number of files that can be combined in a single worker.
#
#
# Created: H. Greenlee, 29-Aug-2012
#
#------------------------------------------------------------------

# Parse arguments.

TFILE=""
NFILE=10000
ARGS=""
UPS_PRDS=""
REL=""
QUAL=""
LOCALDIR=""
LOCALTAR=""
INTERACTIVE=0
GRP=""
WORKDIR=""
OUTDIR=""
LOGDIR=""
SCRATCH=""
CLUS=""
PROC=""
PROCMAP=""
INITSCRIPT=""
INITSOURCE=""
ENDSCRIPT=""
SAM_USER=$GRID_USER
SAM_GROUP=""
SAM_STATION=""
SAM_DEFNAME=""
SAM_PROJECT=""
SAM_START=0
RECUR=0
SAM_SCHEMA=""
OS=""
IFDH_OPT=""
INIT=""
declare -a DATAFILETYPES

while [ $# -gt 0 ]; do
  case "$1" in

    # Help.
    -h|--help )
      awk '/^# Usage:/,/^# End options/{print $0}' $0 | cut -c3- | head -n -2
      exit
      ;;

    # Config file (for compatibility -- ignored).
    -c|--config )
      if [ $# -gt 1 ]; then
        shift
      fi
      ;;

    # Number of events (for compabitility -- ignored).
    -n|--nevts )
      if [ $# -gt 1 ]; then
        shift
      fi
      ;;

    # Output TFile.
    -T|--TFileName )
      if [ $# -gt 1 ]; then
        TFILE=$2
        shift
      fi
      ;;    

    # Number of files to process.
    --nfile )
      if [ $# -gt 1 ]; then
        NFILE=$2
        shift
      fi
      ;;

    # Specify data file types (repeatable).
    --data_file_type )
      if [ $# -gt 1 ]; then
        ntype=${#DATAFILETYPES[@]}
        DATAFILETYPES[$ntype]=$2
	shift
      fi
      ;;

    # Sam user.
    --sam_user )
      if [ $# -gt 1 ]; then
        SAM_USER=$2
        shift
      fi
      ;;

    # Sam group.
    --sam_group )
      if [ $# -gt 1 ]; then
        SAM_GROUP=$2
        shift
      fi
      ;;

    # Sam station.
    --sam_station )
      if [ $# -gt 1 ]; then
        SAM_STATION=$2
        shift
      fi
      ;;

    # Sam dataset definition name.
    --sam_defname )
      if [ $# -gt 1 ]; then
        SAM_DEFNAME=$2
        shift
      fi
      ;;

    # Sam project name.
    --sam_project )
      if [ $# -gt 1 ]; then
        SAM_PROJECT=$2
        shift
      fi
      ;;

    # Sam start/stop project flag.
    --sam_start )
      SAM_START=1
      ;;

    # Recursive flag.
    --recur )
      RECUR=1
      ;;

    # Sam schema.
    --sam_schema )
      if [ $# -gt 1 ]; then
        SAM_SCHEMA=$2
        shift
      fi
      ;;

    # OS.
    --os )
      if [ $# -gt 1 ]; then
        OS=$2
        shift
      fi
      ;;

    # General arguments for hadd command line.
    --args )
      if [ $# -gt 1 ]; then
        shift
        ARGS=$@
        break
      fi
      ;;

    # Top level ups products (comma-separated list).
    --ups )
      if [ $# -gt 1 ]; then
        UPS_PRDS=$2
        shift
      fi
      ;;

    # Release tag.
    -r|--release )
      if [ $# -gt 1 ]; then
        REL=$2
        shift
      fi
      ;;

    # Release build qualifier.
    -q|-b|--build )
      if [ $# -gt 1 ]; then
        QUAL=$2
        shift
      fi
      ;;

    # Local test release directory.
    --localdir )
      if [ $# -gt 1 ]; then
        LOCALDIR=$2
        shift
      fi
      ;;

    # Local test release tarball.
    --localtar )
      if [ $# -gt 1 ]; then
        LOCALTAR=$2
        shift
      fi
      ;;

    # MRB flag.
    --mrb )
      ;;

    # SRT flag.
    --srt )
      echo "SRT run time environment is no longer supported."
      exit 1
      ;;

    # Interactive flag.
    -i|--interactive )
      INTERACTIVE=1
      ;;

    # Grid flag (no effect).
    -g|--grid )
      ;;

    # Group.
    --group )
      if [ $# -gt 1 ]; then
        GRP=$2
        shift
      fi
      ;;

    # Work directory.
    --workdir )
      if [ $# -gt 1 ]; then
        WORKDIR=$2
        shift
      fi
      ;;

    # Output directory.
    --outdir )
      if [ $# -gt 1 ]; then
        OUTDIR=$2
        shift
      fi
      ;;

    # Log directory.
    --logdir )
      if [ $# -gt 1 ]; then
        LOGDIR=$2
        shift
      fi
      ;;

    # Scratch directory.
    --scratch )
      if [ $# -gt 1 ]; then
        SCRATCH=$2
        shift
      fi
      ;;

    # Job cluster.
    --cluster )
      if [ $# -gt 1 ]; then
        CLUS=$2
        shift
      fi
      ;;

    # Process within cluster.
    --process )
      if [ $# -gt 1 ]; then
        PROC=$2
        shift
      fi
      ;;

    # Process map.
    --procmap )
      if [ $# -gt 1 ]; then
        PROCMAP=$2
        shift
      fi
      ;;

    # User initialization script.
    --init-script )
      if [ $# -gt 1 ]; then
        INITSCRIPT=$2
        shift
      fi
      ;;

    # User source initialization script.
    --init-source )
      if [ $# -gt 1 ]; then
        INITSOURCE=$2
        shift
      fi
      ;;

    # User end-of-job script.
    --end-script )
      if [ $# -gt 1 ]; then
        ENDSCRIPT=$2
        shift
      fi
      ;;

    # Specify environment initialization script path.
    --init )
      if [ $# -gt 1 ]; then
        INIT=$2
        shift
      fi
      ;;

    # Other.
    * )
      echo "Unknown option $1"
      exit 1
  esac
  shift
done

#echo "TFILE=$TFILE"
#echo "NFILE=$NFILE"
#echo "ARGS=$ARGS"
#echo "REL=$REL"
#echo "QUAL=$QUAL"
#echo "LOCALDIR=$LOCALDIR"
#echo "LOCALTAR=$LOCALTAR"
#echo "INTERACTIVE=$INTERACTIVE"
#echo "GRP=$GRP"
#echo "WORKDIR=$WORKDIR"
#echo "OUTDIR=$OUTDIR"
#echo "LOGDIR=$LOGDIR"
#echo "SCRATCH=$SCRATCH"
#echo "CLUS=$CLUS"
#echo "PROC=$PROC"
#echo "INITSCRIPT=$INITSCRIPT"
#echo "INITSOURCE=$INITSOURCE"
#echo "ENDSCRIPT=$ENDSCRIPT"

# Set default data file types ("root").

if [ ${#DATAFILETYPES[@]} -eq 0 ]; then
  DATAFILETYPES[0]=root
fi

# Done with arguments.

echo "Nodename: `hostname -f`"
id
echo "Load average:"
cat /proc/loadavg

# Set defaults.

if [ x$QUAL = x ]; then
  QUAL="prof:e9"
fi

if [ x$SAM_GROUP = x ]; then
  SAM_GROUP=$GRP
fi

if [ x$SAM_STATION = x ]; then
  SAM_STATION=$GRP
fi

# Standardize sam_schema (xrootd -> root, xroot -> root).

if [ x$SAM_SCHEMA = xxrootd ]; then
  SAM_SCHEMA=root
fi
if [ x$SAM_SCHEMA = xxroot ]; then
  SAM_SCHEMA=root
fi

# Make sure work directory is defined and exists.

if [ x$WORKDIR = x ]; then
  echo "Work directory not specified."
  exit 1
fi
echo "Work directory: $WORKDIR"

# Initialize experiment ups products and mrb.

echo "Initializing ups and mrb."

if [ x$INIT != x ]; then
  if [ ! -f $INIT ]; then
    echo "Environment initialization script $INIT not found."
    exit 1
  fi
  echo "Sourcing $INIT"
  source $INIT
else
  echo "Sourcing setup_experiment.sh"
  source ${CONDOR_DIR_INPUT}/setup_experiment.sh
fi

echo PRODUCTS=$PRODUCTS

# Ifdh may already be setup by jobsub wrapper.
# If not, set it up here.

echo "IFDHC_DIR=$IFDHC_DIR"
if [ x$IFDHC_DIR = x ]; then
  echo "Setting up ifdhc, because jobsub did not set it up."
  setup ifdhc
fi
echo "IFDHC_DIR=$IFDHC_DIR"

# Set GROUP environment variable.

unset GROUP
if [ x$GRP != x ]; then
  GROUP=$GRP
else
  echo "GROUP not specified."
  exit 1  
fi
export GROUP
echo "Group: $GROUP"

echo "IFDH_OPT=$IFDH_OPT"

# Make sure output directory exists and is writable.

if [ x$OUTDIR = x ]; then
  echo "Output directory not specified."
  exit 1
fi
echo "Output directory: $OUTDIR"

# Make sure log directory exists and is writable.

if [ x$LOGDIR = x ]; then
  echo "Log directory not specified."
  exit 1
fi
echo "Log directory: $LOGDIR"

# Make sure scratch directory is defined.
# For batch, the scratch directory is always $_CONDOR_SCRATCH_DIR
# For interactive, the scratch directory is specified by option 
# --scratch or --outdir.

if [ $INTERACTIVE -eq 0 ]; then
  SCRATCH=$_CONDOR_SCRATCH_DIR
else
  if [ x$SCRATCH = x ]; then
    SCRATCH=$OUTDIR
  fi
fi
if [ x$SCRATCH = x -o ! -d "$SCRATCH" -o ! -w "$SCRATCH" ]; then
  echo "Local scratch directory not defined or not writable."
  exit 1
fi

# Create the scratch directory in the condor scratch diretory.
# Copied from condor_lBdetMC.sh.
# Scratch directory path is stored in $TMP.
# Scratch directory is automatically deleted when shell exits.

# Do not change this section.
# It creates a temporary working directory that automatically cleans up all
# leftover files at the end.
TMP=`mktemp -d ${SCRATCH}/working_dir.XXXXXXXXXX`
TMP=${TMP:-${SCRATCH}/working_dir.$$}

{ [[ -n "$TMP" ]] && mkdir -p "$TMP"; } || \
  { echo "ERROR: unable to create temporary directory!" 1>&2; exit 1; }
trap "[[ -n \"$TMP\" ]] && { rm -rf \"$TMP\"; }" 0
cd $TMP
# End of the section you should not change.

echo "Scratch directory: $TMP"

# Copy files from work directory to scratch directory.

echo "No longer fetching files from work directory."
echo "that's now done with using jobsub -f commands"
mkdir work
cp ${CONDOR_DIR_INPUT}/* ./work/
cd work
echo "Local working directoroy:"
pwd
ls
echo

# Save the hostname and condor job id.

hostname > hostname.txt
echo ${CLUSTER}.${PROCESS} > jobid.txt

# Set default CLUSTER and PROCESS environment variables for interactive jobs.

if [ $INTERACTIVE -ne 0 ]; then
  CLUSTER=`date +%s`   # From time stamp.
  PROCESS=0            # Default zero for interactive.
fi

# Override CLUSTER and PROCESS from command line options.

if [ x$CLUS != x ]; then
  CLUSTER=$CLUS
fi
if [ x$PROC != x ]; then
  PROCESS=$PROC
fi
if [ x$PROCMAP != x ]; then
  if [ -f $PROCMAP ]; then
    PROCESS=`sed -n $(( $PROCESS + 1 ))p $PROCMAP`
  else
    echo "Process map file $PROCMAP not found."
    exit 1
  fi
fi
if [ x$CLUSTER = x ]; then
  echo "CLUSTER not specified."
  exit 1
fi
if [ x$PROCESS = x ]; then
  echo "PROCESS not specified."
  exit 1
fi
echo "Procmap: $PROCMAP"
echo "Cluster: $CLUSTER"
echo "Process: $PROCESS"

# Construct name of output subdirectory.

OUTPUT_SUBDIR=${CLUSTER}_${PROCESS}
echo "Output subdirectory: $OUTPUT_SUBDIR"

# Make sure init script exists and is executable (if specified).

if [ x$INITSCRIPT != x ]; then
  if [ -f "$INITSCRIPT" ]; then
    chmod +x $INITSCRIPT
  else
    echo "Initialization script $INITSCRIPT does not exist."
    exit 1
  fi
fi

# Make sure init source script exists (if specified).

if [ x$INITSOURCE != x -a ! -f "$INITSOURCE" ]; then
  echo "Initialization source script $INITSOURCE does not exist."
  exit 1
fi

# Make sure end-of-job script exists and is executable (if specified).

if [ x$ENDSCRIPT != x ]; then
  if [ -f "$ENDSCRIPT" ]; then
    chmod +x $ENDSCRIPT
  else
    echo "Initialization script $ENDSCRIPT does not exist."
    exit 1
  fi
fi

# MRB run time environment setup goes here.

# Setup local test release, if any.

if [ x$LOCALDIR != x ]; then
  mkdir $TMP/local
  cd $TMP/local

  # Copy test release directory recursively.

  echo "Copying local test release from directory ${LOCALDIR}."

  # Make sure ifdhc is setup.

  if [ x$IFDHC_DIR = x ]; then
    echo "Setting up ifdhc before fetching local directory."
    setup ifdhc
  fi
  echo "IFDHC_DIR=$IFDHC_DIR"
  ifdh cp -r $IFDH_OPT $LOCALDIR .
  stat=$?
  if [ $stat -ne 0 ]; then
    echo "ifdh cp failed with status ${stat}."
    exit $stat
  fi
  find . -name \*.py -exec chmod +x {} \;
  find . -name \*.sh -exec chmod +x {} \;

  # Setup the environment.

  cd $TMP/work
  echo "Initializing localProducts from ${LOCALDIR}."
  if [ ! -f $TMP/local/setup ]; then
    echo "Local test release directory $LOCALDIR does not contain a setup script."
    exit 1
  fi
  sed "s@setenv MRB_INSTALL.*@setenv MRB_INSTALL ${TMP}/local@" $TMP/local/setup | \
  sed "s@setenv MRB_TOP.*@setenv MRB_TOP ${TMP}@" > $TMP/local/setup.local
  . $TMP/local/setup.local
  #echo "MRB_INSTALL=${MRB_INSTALL}."
  #echo "MRB_QUALS=${MRB_QUALS}."
  echo "Setting up all localProducts."
  if [ x$IFDHC_DIR != x ]; then
    unsetup ifdhc
  fi
  mrbslp
fi
cd $TMP/work

# Setup local larsoft test release from tarball.

if [ x$LOCALTAR != x ]; then
  mkdir $TMP/local
  cd $TMP/local

  # Fetch the tarball.

  echo "Fetching test release tarball ${LOCALTAR}."

  # Make sure ifdhc is setup.

  if [ x$IFDHC_DIR = x ]; then
    echo "Setting up ifdhc before fetching tarball."
    setup ifdhc
  fi
  echo "IFDHC_DIR=$IFDHC_DIR"
  ifdh cp $LOCALTAR local.tar
  stat=$?
  if [ $stat -ne 0 ]; then
    echo "ifdh cp failed with status ${stat}."
    exit $stat
  fi 

  # Extract the tarball.

  tar -xf local.tar

  # Setup the environment.

  cd $TMP/work
  echo "Initializing localProducts from tarball ${LOCALTAR}."
  sed "s@setenv MRB_INSTALL.*@setenv MRB_INSTALL ${TMP}/local@" $TMP/local/setup | \
  sed "s@setenv MRB_TOP.*@setenv MRB_TOP ${TMP}@" > $TMP/local/setup.local
  . $TMP/local/setup.local
  #echo "MRB_INSTALL=${MRB_INSTALL}."
  #echo "MRB_QUALS=${MRB_QUALS}."
  echo "Setting up all localProducts."
  if [ x$IFDHC_DIR != x ]; then
    unsetup ifdhc
  fi
  mrbslp
fi

# Setup specified version of top level run time products
# (if specified, and if local test release did not set them up).

if [ x$IFDHC_DIR != x ]; then
  unsetup ifdhc
fi

for prd in `echo $UPS_PRDS | tr , ' '`
do
  if ! ups active | grep -q $prd; then
    echo "Setting up $prd $REL -q ${QUAL}."
    setup $prd $REL -q $QUAL
  fi
done

ups active

cd $TMP/work

# In case mrb setup didn't setup a version of ifdhc, set up ifdhc again.

if [ x$IFDHC_DIR = x ]; then
  echo "Setting up ifdhc again, because larsoft did not set it up."
  setup ifdhc
fi
echo "IFDH_ART_DIR=$IFDH_ART_DIR"
echo "IFDHC_DIR=$IFDHC_DIR"

# Start project (if necessary), and consumer process.

PURL=''
CPID=''

# Make sure a project name has been specified.

if [ x$SAM_PROJECT = x ]; then
  echo "No sam project was specified."
  exit 1
fi
echo "Sam project: $SAM_PROJECT"

# Start project (if requested).

if [ $SAM_START -ne 0 ]; then

  # If recursive flag, take snapshot of input dataset.

  if [ $RECUR -ne 0 ]; then
    echo "Forcing snapshot"
    SAM_DEFNAME=${SAM_DEFNAME}:force
  fi

  # Start the project.

  if [ x$SAM_DEFNAME != x ]; then

    echo "Starting project $SAM_PROJECT using sam dataset definition $SAM_DEFNAME"
    ifdh startProject $SAM_PROJECT $SAM_STATION $SAM_DEFNAME $SAM_USER $SAM_GROUP
    if [ $? -eq 0 ]; then
      echo "Start project succeeded."
    else
      echo "Start projet failed."
      exit 1
    fi
  else
    echo "Start project requested, but no definition was specified."
    exit 1
  fi
fi

# Get the project url of a running project (maybe the one we just started,
# or maybe started externally).  This command has to succeed, or we can't
# continue.

PURL=`ifdh findProject $SAM_PROJECT $SAM_STATION`
if [ x$PURL = x ]; then
  echo "Unable to find url for project ${SAM_PROJECT}."
  exit 1
else
  echo "Project url: $PURL"
fi

# Start the consumer process.  This command also has to succeed.

NODE=`hostname`
APPFAMILY=root
APPNAME=hadd

echo "Starting consumer process."
echo "ifdh establishProcess $PURL $APPNAME $REL $NODE $SAM_USER $APPFAMILY hadd $NFILE $SAM_SCHEMA"
CPID=`ifdh establishProcess $PURL $APPNAME $REL $NODE $SAM_USER $APPFAMILY hadd $NFILE $SAM_SCHEMA`
if [ x$CPID = x ]; then
  echo "Unable to start consumer process for project url ${PURL}."
  exit 1
else
  echo "Consumer process id $CPID"
fi

# Stash away the project name and consumer process id in case we need them
# later for bookkeeping.

echo $SAM_PROJECT > sam_project.txt
echo $CPID > cpid.txt

# Run/source optional initialization scripts.

if [ x$INITSCRIPT != x ]; then
  echo "Running initialization script ${INITSCRIPT}."
  if ! ./${INITSCRIPT}; then
    exit $?
  fi
fi
if [ x$INITSOURCE != x ]; then
  echo "Sourcing initialization source script ${INITSOURCE}."
  . $INITSOURCE
  status=$?
  if [ $status -ne 0 ]; then
    exit $status
  fi
fi

# Save a copy of the environment, which can be helpful for debugging.

env > env.txt

# Fetch files and construct local input list.
# Keep going until we have fetched $NFILE files or no more files are available.

rm -f condor_hadd_input.list
rm -f transferred_uris.list
touch condor_hadd_input.list
touch transferred_uris.list

while [ $NFILE -gt 0 ]
do
  NFILE=$(( $NFILE - 1 ))

  # Get uri of the next file

  fileuri=`ifdh getNextFile $PURL $CPID`
  stat=$?
  if [ $stat != 0 ]; then
    echo "ifdh getNextFile returned status $stat"
    break
  fi
  if [ x$fileuri = x ]; then
    echo "ifdh getNextFile did not return anything."
    break
  fi

  # Break out of the loop if the same uri is returned twice.

  if grep -q $fileuri transferred_uris.list; then
    echo "File $filename was returned twice by sam."
    break
  fi

  # Find the local path to which this uri will be fetched.

  filepath=$fileuri
  if [[ ! $fileuri =~ ^root: ]]; then
    filepath=`ifdh localPath $fileuri`
    stat=$?
    if [ $stat != 0 ]; then
      echo "ifdh localPath returned status $stat"
      break
    fi
    if [ x$filepath = x ]; then
      echo "ifdh localPath did not return anything."
      break
    fi

    # Transfer the file.

    ifdh fetchInput $fileuri
    stat=$?
    if [ $stat != 0 ]; then
      echo "ifdh fetchInput returned status $stat"
      break
    fi
    if [ ! -f $filepath ]; then
      echo "Transferred file $fileuri not found."
      break
    fi
  fi

  # If we get to here, file has been transferred successfully.
  # Update the file status to consumed.

  filename=`basename $filepath`
  ifdh updateFileStatus $PURL $CPID $filename consumed

  # Update file lists.

  echo $fileuri >> transferred_uris.list
  echo $filepath >> condor_hadd_input.list

done

# Run hadd.

hadd $TFILE @condor_hadd_input.list
stat=$?
echo $stat > hadd.stat
echo $stat > lar.stat
echo "hadd completed with exit status ${stat}."

# Setup up current version of ifdhc (may be different than version setup by larsoft).

#echo "Setting up current version of ifdhc."
#if [ x$IFDHC_DIR != x ]; then
#  unsetup ifdhc
#fi
#setup ifdhc v1_3_2
echo "IFDHC_DIR=$IFDHC_DIR"

# Sam cleanups.
# Get list of consumed files.

ifdh translateConstraints "consumer_process_id $CPID and consumed_status consumed" > consumed_files.list

# End consumer process.

ifdh endProcess $PURL $CPID

# Stop project (if appropriate).

if [ $SAM_START -ne 0 ]; then
  echo "Stopping project."
  ifdh endProject $PURL
fi

# Delete input files.

if [ -f condor_hadd_input.list -a x$SAM_SCHEMA != xroot ]; then
  while read file; do
    rm -f $file
  done < condor_hadd_input.list
fi

# Run optional end-of-job script.

if [ x$ENDSCRIPT != x ]; then
  echo "Running end-of-job script ${ENDSCRIPT}."
  if ! ./${ENDSCRIPT}; then
    exit $?
  fi
fi

# Do root file checks.

# Randomize the names of the output root files.
for root in *.root; do
  base=`basename $root .root`_`uuidgen`
  mv $root ${base}.root
  if [ -f ${root}.json ]; then
    mv ${root}.json ${base}.root.json
  fi
done

# Calculate root metadata for all root files and save as json file.
# If json metadata already exists, merge with newly geneated root metadata.

for root in *.root; do
  if [ -f $root ]; then
    json=${root}.json
    if [ -f $json ]; then
      ./root_metadata.py --output="${json}2" $root >& /dev/null
      ./merge_json.py $json ${json}2 > ${json}3
      mv -f ${json}3 $json
      rm ${json}2
    else
      ./root_metadata.py --output="$json" $root >& /dev/null
    fi
  fi
done

# Make local output directories for files that don't have a subrun.

mkdir out
mkdir log

# Stash all of the files we want to save in a local directories that we just created.

# First move .root and corresponding .json files into the out and log subdirectories.

for root in *.root; do
  if [ -f $root ]; then
    mv $root out
    if [ -f ${root}.json ]; then
      mv ${root}.json log
    fi
  fi
done

# Copy any remaining files into all log subdirectories.
# These small files get replicated.

for outfile in *; do
  if [ -f $outfile ]; then
    mv $outfile log
  fi
done

# Make a tarball of the log directory contents, and save the tarball in the log directory.

rm -f log.tar
tar -cjf log.tar -C log .
mv log.tar log

# Create remote output and log directories.

export IFDH_CP_MAXRETRIES=5

echo "Make directory ${LOGDIR}/${OUTPUT_SUBDIR}."
date
ifdh mkdir $IFDH_OPT ${LOGDIR}/$OUTPUT_SUBDIR
echo "Done making directory ${LOGDIR}/${OUTPUT_SUBDIR}."
date

if [ ${OUTDIR} != ${LOGDIR} ]; then
  echo "Make directory ${OUTDIR}/${OUTPUT_SUBDIR}."
  date
  ifdh mkdir $IFDH_OPT ${OUTDIR}/$OUTPUT_SUBDIR
  echo "Done making directory ${OUTDIR}/${OUTPUT_SUBDIR}."
  date
fi

# Transfer tarball in log subdirectory.

statout=0
echo "ls log"
ls log
echo "ifdh cp -D $IFDH_OPT log/log.tar ${LOGDIR}/$OUTPUT_SUBDIR"
ifdh cp -D $IFDH_OPT log/log.tar ${LOGDIR}/$OUTPUT_SUBDIR
date
stat=$?
if [ $stat -ne 0 ]; then
  statout=1
  echo "ifdh cp failed with status ${stat}."
fi

# Transfer root files in out subdirectory.

if [ "$( ls -A out )" ]; then
  echo "ifdh cp -D $IFDH_OPT out/* ${OUTDIR}/$OUTPUT_SUBDIR"
  ifdh cp -D $IFDH_OPT out/* ${OUTDIR}/$OUTPUT_SUBDIR
  stat=$?
  if [ $stat -ne 0 ]; then
    statout=1
    echo "ifdh cp failed with status ${stat}."
  fi
fi

if [ $statout -eq 0 -a -f log/hadd.stat ]; then
  statout=`cat log/hadd.stat`
fi

exit $statout
