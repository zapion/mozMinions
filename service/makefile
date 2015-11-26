work_dir = /tmp/minion_job
install_dir = $(shell cd ..;pwd)
job_dir = ${install_dir}/conf/crash
user = $(shell whoami)
is_install = $(shell test -f last_install && echo yes)
install:
ifeq ($(is_install),yes)
	$(error installed already)
endif
	cp minion_service backup
	sed -i 's|%WORK%|${work_dir}|' backup
	sed -i 's|%INS%|${install_dir}|' backup
	sed -i 's|%JOB%|${job_dir}|' backup
	sudo cp backup /etc/init.d/minion_service
	mv backup last_install
	/etc/init.d/minion_service start

uninstall:
ifneq ($(is_install),yes)
	$(error not installed)
endif
	/etc/init.d/minion_service stop
	sudo rm /etc/init.d/minion_service
	rm last_install
