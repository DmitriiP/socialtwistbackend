#!/usr/bin/env bash
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

SESSION=st-workspace

tmux new-session -d -s $SESSION

tmux new-window -n nginx tail -F /var/log/nginx/twist.log
tmux select-window -t $SESSION:nginx
tmux split-window -h cd /var/lib/nginx/body/

tmux new-window -n database su twist -c "psql -d social_twist"

tmux new-window -n django tail -F /home/twist/server.log
tmux select-window -t $SESSION:django
tmux split-window -h su twist -c "source /home/twist/env/bin/activate; cd /home/twist/social_twist; ./manage.py shell;"
tmux split-window -v -l 5 su twist; source /home/twist/env/bin/activate; cd /home/twist/social_twist
tmux select-pane -t :.1


tmux kill-window -t $SESSION:0

tmux new-window -n curl
