# this script must be sourced

usage()
{
   echo "USAGE: source grid_setup.sh <product_dir>"
   echo "       sets up all ups products found in <product_dir>"
   echo ""
   echo " This script is designed to be used when copying a localProducts directory"
   echo " to the grid for testing."
   echo " DO NOT setup mrb when using this script."
   echo ""
}

get_this_dir()
{
    ( cd / ; /bin/pwd -P ) >/dev/null 2>&1
    if (( $? == 0 )); then
      pwd_P_arg="-P"
    fi
echo "bash source $BASH_SOURCE"
    reldir=`dirname "$BASH_SOURCE"`
    thisdir=`cd ${reldir} && /bin/pwd ${pwd_P_arg}`
}

MRB_INSTALL=${1}

test $?shell = 1 && set ss=csh || ss=sh
echo Shell type is $ss.

if [ -z ${MRB_INSTALL} ]
then
   echo "ERROR: please specify the product directory"
   usage
   return 1
fi

if [ -n "${MRB_BUILDDIR}" ]; then
   echo "ERROR: the mrb development environment is enabled."
   echo "ERROR: please run this script in a clean environment."
   return 1
fi
if [ -n "${MRB_SOURCE}" ]; then
   echo "ERROR: the mrb development environment is enabled."
   echo "ERROR: please run this script in a clean environment."
   return 1
fi

if [ ! -d ${MRB_INSTALL} ]
then
   echo "ERROR: cannot find ${MRB_INSTALL}"
   usage
   return 1
fi

get_this_dir

if [ -z ${UPS_DIR} ]
then
   echo "ERROR: please setup ups"
   return 1
fi
source `${UPS_DIR}/bin/ups setup ${SETUP_UPS}`

localP=$MRB_INSTALL

##echo
##ups active
##echo

tmpfl=/tmp/`basename $localP`_setup_$$$$
rm -f $tmpfl
echo > $tmpfl
echo "## checking $localP for products" >> $tmpfl
echo "source \`${UPS_DIR}/bin/ups setup ${SETUP_UPS}\`" >> $tmpfl

# deal with UPS_OVERRIDE
echo "# incoming UPS_OVERRIDE $UPS_OVERRIDE"  >> $tmpfl
if [ -z "${UPS_OVERRIDE}" ]; then
   new_override="-B"
else 
   tempover=`echo ${UPS_OVERRIDE} | sed -e 's/\-B//'`
   new_override="-B ${tempover}"
fi
echo "export UPS_OVERRIDE=\"${new_override}\""  >> $tmpfl

ups list -aK+ -z $localP | while read line
do
  ##echo "got line: $line"
  words=($(echo $line | tr " " "\n"))
  ##echo "split into ${#words[@]} pieces"
  product=$(echo ${words[0]} | tr "\"" " ")
  version=$(echo ${words[1]} | tr "\"" " ")
  quals=$(echo ${words[3]} | tr "\"" " ")
  product_uc=$(echo ${product} | tr '[a-z]' '[A-z]')
  echo "product_setup=\$(printenv | grep SETUP_${product_uc} | wc -l)" >> $tmpfl
  echo "if [[ \"\${product_setup}\" > 0 ]]; then"  >> $tmpfl
  echo "unsetup -j $product"  >> $tmpfl
  echo "fi"  >> $tmpfl
  if [ -z $quals ]
  then
      cmd="setup -B $product  $version"
  else
      pq=+`echo ${quals} | sed -e 's/:/:+/g'`
      cmd="setup -B $product  $version -q $pq"
  fi
  echo "$cmd -z $localP:${PRODUCTS}" >> $tmpfl
done

echo "ready to source $tmpfl"
source $tmpfl


return 0
