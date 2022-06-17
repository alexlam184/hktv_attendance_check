#!/bin/sh

#while true; do
#	read -r -p "Half day work? [Y/N] " isHalfDay
#	case $isHalfDay in
#		[yY] | [nN])
#			break
#			;;
#		*)
#			echo wrong input, please try again
#			;;
#	esac
#done

isHalfDay=$1

# COLOR

GREEN='\033[0;30;42m'
BLUE='\033[1;44m'
NC='\033[0m' # No Color

# change here base64
username=YWxhbQ==
password=SEtUVi0xMjM=

alias jq='/d/personal/attendance_check/jq-win64.exe'

cookies=.cookies.tmp

timestamp=`date +"%Y-%m-%d %H:%M"`
yyyymmdd=${timestamp:0:10}
dd=${yyyymmdd:8:2}
mm=${yyyymmdd:5:2}
yyyy=${yyyymmdd:0:4}
HH=${timestamp:11:2}
MM=${timestamp:14:2}

if [[ $dd -gt 15 ]]; then
	mm=$(( $mm + 1 ))
	if [[ $mm -gt 12 ]]; then
		mm=01
		yyyy=$(( $yyyy + 1 ))
	fi
fi

curl -s -c ${cookies} -d "action=login&fldEmpLoginID=`echo -n ${username} | base64 -d`&fldEmpPwd=`echo -n ${password} | base64 -d`&code=undefined" -X POST "https://hrms.hktv.com.hk/api/admin/login" > /dev/null

in=`curl -s -c ${cookies} -b ${cookies} -X GET "https://hrms.hktv.com.hk/api/Attendance/getpages?page=1&limit=31&types=1&fldMonth=${yyyy}-${mm}&fldCatID=&fldBranch=&fldEmpPosition=" | jq --raw-output --arg now ${yyyymmdd} '.data|map(select(.fldDate == $now))[]|.fldDate,.fldIn1'`

curl -s -c ${cookies} -d "" -b ${cookies} -X POST "https://hrms.hktv.com.hk/api/Admin/LogOut" > /dev/null

rm ${cookies}

in=`echo $in | tr --delete '\r\n'`

if [[ ${in:11:5} == "null" ]]; then
	echo No time retrieved. Try later......
	exit 1
fi

inDate=${in:0:10}
inTime=${in:11:5}
echo $inDate
echo $inTime

if [[ $isHalfDay != [hH] ]]; then
	targetTime=`date -d "${inTime:0:2}${inTime:3:2}+9hour" +"%H%M"`
else
	targetTime=`date -d "${inTime:0:2}${inTime:3:2}+3hour+30minute" +"%H%M"`
fi

timeLeft=`date -d "$targetTime-${HH}hour-${MM}minute" +"%H:%M:%S"` 
hoursLeft=`date -d "$targetTime-${HH}hour-${MM}minute" +"%-H"`
#minutesLeft=`date -d "$targetTime-${HH}hour-${MM}minute" +"%-M"`
while [[ -z $key ]]; do
	if [[ $hoursLeft -gt 9 ]]; then
		#echo ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAuJycuICAgICAgIAogICAgICAgLicnLiAgICAgIC4gICAgICAgIConJyogICAgOl9cL186ICAgICAuIAogICAgICA6X1wvXzogICBfXCgvXyAgLjouKl9cL18qICAgOiAvXCA6ICAuJy46LicuCiAgLicnLjogL1wgOiAgIC4vKVwgICAnOicqIC9cICogOiAgJy4uJy4gIC09Om86PS0KIDpfXC9fOicuOjo6LiAgICAnIConJyogICAgKiAnLlwnLy4nIF9cKC9fJy4nOicuJwogOiAvXCA6IDo6Ojo6ICAgICAqX1wvXyogICAgIC09IG8gPS0gIC8pXCAgICAnICAqCiAgJy4uJyAgJzo6OicgICAgICogL1wgKiAgICAgLicvLlwnLiAgICcKICAgICAgKiAgICAgICAgICAgICouLiogICAgICAgICA6CiAgICAgICAgKgogICAgICAgICo= | base64 -d
		echo -e "\r\033[K"
		echo -e "                                   .''.       \n       .''.      .        *''*    :_\/_:     . \n      :_\/_:   _\(/_  .:.*_\/_*   : /\ :  .'.:.'.\n  .''.: /\ :   ./)\   ':'* /\ * :  '..'.  -=:o:=-\n :_\/_:'.:::.    ' *''*    * '.\'/.' _\(/_'.':'.'\n : /\ : :::::     *_\/_*     -= o =-  /)\    '  *\n  '..'  ':::'     * /\ *     .'/.\'.   '\n      *            *..*         :\n        *\n        *\n"
		echo -e -n "HoOrAyyYYyYYYYYYY!!!!"
		break
	else
		echo -e ${GREEN}Target: ${targetTime:0:2}:${targetTime:2:2}
		echo -e "Press q to exit...${NC}"
		while true; do		
			timestamp=`date +"%H:%M:%-S"`
			
			HH=${timestamp:0:2}
			MM=${timestamp:3:2}
			
			hoursLeft=`date -d "$targetTime-${HH}hour-${MM}minute" +"%-H"`
			minutesLeft=`date -d "$targetTime-${HH}hour-${MM}minute" +"%-M"`
			secondsLeft=$(( 60 - ${timestamp:6} ))

			if [[ $hoursLeft -gt 9 ]]; then
				break
			fi
			echo -e -n "\r\033[K${BLUE}$hoursLeft hours $minutesLeft minutes $(( ${secondsLeft} < 59 ? ${secondsLeft} : 0 )) seconds left${NC}"
			
			read -s -r -t 1 -n 1 key
			if [[ $key == q ]]; then
				break
			fi
		done
	fi
done

echo -e "\n"
