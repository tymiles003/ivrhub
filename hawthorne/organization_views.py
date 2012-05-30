''' organization_views
info about the organzations
'''

from flask import (render_template, request, flash, redirect, url_for, session
    , abort, escape)

from decorators import *
from models import *
import utilities
from hawthorne import app


@app.route('/organizations/', defaults={'org_label': None})
@app.route('/organizations/<org_label>', methods=['GET', 'POST'])
@verification_required
def organizations(org_label):
    ''' show the organizations
    if there's a label included in the route, render that organization alone
    '''
    user = User.objects(email=session['email'])[0]

    if request.method == 'POST':
        orgs = Organization.objects(label=org_label)
        if not orgs:
            abort(404)
        org = orgs[0]
        
        # permission-check
        if org not in user.organizations and not user.admin_rights:
            app.logger.error('%s tried to edit an organization but was \
                denied for want of admin rights' % session['email'])
            abort(404)

        form_type = request.form.get('form_type', '')
        if form_type == 'info':
            if org.name != request.form.get('name', ''):
                app.logger.info('%s edited the name of %s to %s' % (
                    session['email'], org.name, request.form.get('name', '')))
                name = request.form.get('name', '')
                org.name = name
                org.label = str(escape(name).replace(' ', '-')).lower()
           
            if org.description != request.form.get('description', ''):
                app.logger.info('%s edited the description of %s to %s' % (
                    session['email'], org.name
                    , request.form.get('description', '')))
                org.description = request.form.get('description', '')
            
            if org.location != request.form.get('location', ''):
                app.logger.info('%s edited the location of %s to %s' % (
                    session['email'], org.name
                    , request.form.get('location', '')))
                org.location = request.form.get('location', '')

        elif form_type == 'add_members':
            # push membership
            target = request.form.get('add_member_email', '')
            new_members = User.objects(email=target)
            if not new_members:
                flash('we cannot find "%s", has it been registered?' % \
                    target, 'error')
                return redirect(url_for('organizations', org_label=org.label))

            new_member = new_members[0]
            # already a member?
            if org in new_member.organizations:
                flash('"%s" is already a member of "%s"' % (target, org.name)
                    , 'warning')
                return redirect(url_for('organizations', org_label=org.label))
            
            else:
                # add them
                new_member.update(push__organizations=org)
                flash('successfully added "%s" to "%s"' % (target, org.name)
                    , 'success')
                return redirect(url_for('organizations', org_label=org.label))
        
        elif form_type == 'remove_members':
            # push/pull membership
            target = request.form.get('remove_member_email', '')
            old_members = User.objects(email=target)
            if not old_members:
                flash('we cannot find "%s", has it been registered?' % \
                    target, 'error')
                return redirect(url_for('organizations', org_label=org.label))
            
            old_member = old_members[0]
            # not yet a member?
            if org not in old_member.organizations:
                flash('"%s" is not yet a member of "%s"' % (target, org.name)
                    , 'warning')
                return redirect(url_for('organizations', org_label=org.label))
            else:
                # drop 'em
                old_member.update(pull__organizations=org)
                flash('successfully removed "%s" from %s' % (target, org.name)
                    , 'info')
                return redirect(url_for('organizations', org_label=org.label))

        elif form_type == 'admin':
            # delete the organization; permission-check first
            if not user.admin_rights:
                app.logger.error('%s tried to delete %s but was denied for \
                    want of admin rights' % (session['email'], org.name))
                abort(404)

            # revoke membership first
            members = User.objects(organizations=org)
            for member in members:
                member.update(pull__organizations=org)
            
            # blow away the org itself
            name = org.name
            org.delete()
            app.logger.info('%s deleted %s' % (session['email'], name))
            flash('organization "%s" was deleted' % name, 'success')
            return redirect(url_for('organizations'))
        
        else:
            # bad 'form_type'
            abort(404)
       
        try:
            org.save()
            flash('changes saved successfully', 'success')
        except:
            org.reload()
            app.logger.error('%s experienced an error saving info about %s' % (
                session['email'], request.form['name']))
            flash('Error saving changes, is the name unique?', 'error')
        
        return redirect(url_for('organizations', org_label=org.label
            , edit='true'))

    
    if request.method == 'GET':
        if org_label:
            orgs = Organization.objects(label=org_label)
            if not orgs:
                app.logger.error('%s tried to access an organization that \
                    does not exist' % session['email'])
                flash('Organization "%s" not found, sorry!' % org_label
                    , 'warning')
                return redirect(url_for('organizations'))
            org = orgs[0]

            # permission-check
            if org not in user.organizations and not user.admin_rights:
                app.logger.error('%s tried to access an organization but was \
                    denied for want of admin rights' % session['email'])
                abort(404)

            if request.args.get('edit', '') == 'true':
                users = User.objects(organizations=org)
                return render_template('organization_edit.html'
                    , organization=org, users=users)
            else:
                # get all the members
                users = User.objects(organizations=org)
                return render_template('organization.html', organization=org
                    , users=users)

        if request.args.get('create', '') == 'true':
            # create a new form
            # permissions-check 
            if not user.admin_rights:
                app.logger.error('%s tried to create an organization but was \
                    denied for want of admin rights' % session['email'])
                abort(404)

            try:
                org_name = 'org-%s' % utilities.generate_random_string(6)
                new_org = Organization(
                    label = org_name.lower()
                    , name = org_name
                )
                new_org.save() 
                app.logger.info('organization created by %s' % \
                    session['email'])
                flash('organization created; please change the defaults', 
                    'success')
            except:
                app.logger.error('organization creation failed for %s' % \
                    session['email'])
                flash('There was an error in the form, sorry :/', 'error')
                return redirect(url_for('organizations'))
            
            # redirect to the editing screen
            return redirect(url_for('organizations', org_label=new_org.label
                , edit='true'))
        
        # nobody in particular was specified; show em all
        if user.admin_rights:
            orgs = Organization.objects()
        else:
            orgs = user.organizations

        # find the users for each org
        users = {}
        for org in orgs:
            users[org.name] = User.objects(organizations=org)

        return render_template('organizations.html', organizations=orgs
            , users=users)
