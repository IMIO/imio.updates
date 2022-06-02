#!/usr/bin/make
#

.PHONY: setup
setup:
	virtualenv -p python2 .
	./bin/pip install --upgrade pip
	./bin/pip install -r requirements.txt -e .
	./bin/update_instances

.PHONY: cleanall
cleanall:
	rm -fr bin include lib local share
	git checkout bin

.PHONY: export_users_pst2
export_users:
        ./bin/update_instances -p assesse_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=assesse -v mun_slug=0207350762 -z -d
        ./bin/update_instances -p chatelet_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=chatelet -v mun_slug=0206628707 -z -d
        ./bin/update_instances -p fleron_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=fleron -v mun_slug=0207341557 -z -d
        ./bin/update_instances -p geer_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=geer -v mun_slug=0207376595 -z -d
        ./bin/update_instances -p gembloux_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=gembloux -v mun_slug=0216697505 -z -d
        ./bin/update_instances -p lahulpe_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=lahulpe -v mun_slug=0207282268 -z -d
        ./bin/update_instances -p lalouviere_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=lalouviere -v mun_slug=0871429489 -z -d
        ./bin/update_instances -p mons_cpas_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=mons_cpas -v mun_slug=0207889113 -z -d
        ./bin/update_instances -p ohey_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=ohey -v mun_slug=0207358581 -z -d
        ./bin/update_instances -p orpjauche_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=orpjauche -v mun_slug=0216689783 -z -d
        ./bin/update_instances -p stavelot_cpas_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=stavelot_cpas -v mun_slug=0207403915 -z -d
        ./bin/update_instances -p viroinval_cpas_prj_133 -m install_requests -c /home/zope/export_users/export_plone_users.py -v app_id=iA.PST -v mun_id=viroinval_cpas -v mun_slug=0216761841 -z -d
