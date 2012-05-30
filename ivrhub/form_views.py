''' form_views
creating and editing forms
'''
from flask import (render_template, request, flash, redirect, url_for, session
    , abort, escape)

from decorators import *
from models import *
import utilities
from ivrhub import app

@app.route('/organizations/<org_label>/forms', defaults={'form_label': None})
@app.route('/organizations/<org_label>/forms/<form_label>'
    , methods=['GET', 'POST'])
@verification_required
def forms(org_label, form_label):
    ''' show the forms
    if there's a label included in the route, render that form alone
    '''
    user = User.objects(email=session['email'])[0]
    
    # find the relevant organization
    orgs = Organization.objects(label=org_label)
    if not orgs:
        app.logger.error('%s tried to access an organization that does not \
            exist' % session['email'])
        flash('Organization "%s" not found, sorry!' % org_label, 'warning')
        return redirect(url_for('organizations'))
    org = orgs[0]

    # permission-check
    if org not in user.organizations and not user.admin_rights:
        app.logger.error('%s tried to access an organization but was denied \
            for want of admin rights' % session['email'])
        abort(404)

    if request.method == 'POST':
        if not form_label:
            abort(404)

        forms = Form.objects(label=form_label)
        if not forms:
            app.logger.error('%s tried to access a form that does not \
                exist' % session['email'])
            flash('Form "%s" does not exist, sorry!' % form_label
                , 'warning')
            return redirect(url_for('forms', org_label=org_label))
        form = forms[0]

        form_type = request.form.get('form_type', '')

        if form_type == 'info':
            name = request.form.get('name', '')
            form.name = name
            form.label = str(escape(name).replace(' ', '-')).lower()

            form.description = request.form.get('description', '')

        elif form_type == 'admin':
            # blow away the form itself
            name = form.name
            form.delete()
            app.logger.info('%s deleted %s' % (session['email'], name))
            flash('form "%s" was deleted' % name, 'success')
            return redirect(url_for('organizations', org_label=org.label))
        
        else:
            # bad 'form_type'
            abort(404)
       
        try:
            form.save()
            flash('Changes to this form were saved successfully', 'success')
            return redirect(url_for('forms', org_label=org_label
                , form_label=form.label))
        except:
            app.logger.error('%s experienced an error saving info about form \
                "%s"' % (session['email'], request.form['name']))
            flash('Error saving changes, sorry /:')
            return redirect(url_for('forms', org_label=org_label
                , form_label=form_label))
    
    if request.method == 'GET':
        if form_label:
            forms = Form.objects(label=form_label)
            if not forms:
                app.logger.error('%s tried to access a form that does not \
                    exist' % session['email'])
                flash('Form "%s" does not exist, sorry!' % form_label
                    , 'warning')
                return redirect(url_for('forms', org_label=org_label))
            form = forms[0]

            if request.args.get('edit', '') == 'true':
                return render_template('form_edit.html', form=form)
            
            else:
                return render_template('form.html', form=form)

        if request.args.get('create', '') == 'true':
            # create a new form
            try:
                form_name = 'form-%s' % utilities.generate_random_string(6)
                new_form = Form(
                    label = form_name.lower()
                    , organization = org
                    , name = form_name
                )
                new_form.save() 
                app.logger.info('form created by %s' % session['email'])
                flash('Form created; please change the defaults', 
                    'success')
                # redirect to the editing screen
                return redirect(url_for('forms', org_label=org_label
                    , form_label=new_form.label, edit='true'))
            except:
                app.logger.error('form creation failed for %s' % \
                    session['email'])
                flash('There was an error in the form, sorry :/', 'error')
                return redirect(url_for('forms', org_label=org_label))
            
        
        # nobody in particular was specified; punt for now
        abort(404)
        '''
        if user.admin_rights:
            forms = Form.objects()
        else:
            forms = Form.objects(organization=org)

        return render_template('forms.html', forms=forms)
        '''
