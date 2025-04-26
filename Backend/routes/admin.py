from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from Backend.models.dbconfig import db_connection
from functools import wraps
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFError

admin = Blueprint('admin', __name__)

def admin_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.index'))
        return route_function(*args, **kwargs)
    return wrapper

@admin.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        unhashpass = request.form['password']
        
        conn, cur = db_connection()
        query = '''SELECT apass, apost FROM admin_info WHERE ausername=%s'''
        cur.execute(query, (username,))
        result = cur.fetchone()
        
        if result and check_password_hash(result[0], unhashpass):
            password, post = result
            session['username'] = username
            session['user_type'] = post
            session['admin_logged_in'] = True
            cur.close()
            conn.close()
            
            if post.lower() == 'supervisor':
                return redirect(url_for('admin.supervisor_dashboard_view', supervisor_name=username))
            elif post.lower() == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
        
        cur.close()
        conn.close()
        return render_template('admin/login.html', error="Invalid credentials")
    
    return render_template('admin/login.html')


@admin.route('/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    query='''SELECT c_name, c_address,c_email,c_phone FROM  client_details'''
    conn,cur=db_connection()
    cur.execute(query)
    data=cur.fetchall()
    client_details = [dict(c_name=row[0], c_address=row[1], c_email=row[2], c_phone=row[3]) for row in data]
    print(client_details[0]['c_name'])
    return render_template('admin/dashboard.html', client_details=client_details)


@admin.route('/admin/newuser', methods=['GET', 'POST'])
@admin_required
def new_user():
    if request.method == 'POST':
        location = f"{request.form['address']}, {request.form['city']}, {request.form['state']} - {request.form['pincode']}"
        customer = {
            'name': request.form['name'],
            'location': location,
            'email': request.form['email'],
            'phone': request.form['phone']
        }
        print("New Customer Details:", customer)
        conn,cur=db_connection()
        query='''INSERT INTO client_details(c_name,c_address,c_email,c_phone) VALUES (%s,%s,%s,%s)'''
        cur.execute(query,(customer['name'],customer['location'],customer['email'],customer['phone']))
        conn.commit()
        conn.close()
        cur.close()
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/customer_form.html')

@admin.route('/admin/newsupplier', methods=['GET', 'POST'])
@admin_required
def new_supplier():
    if request.method == 'POST':
        location = f"{request.form['address']}, {request.form['city']}, {request.form['state']} - {request.form['pincode']}"
        supplier = {
            'name': request.form['name'],
            'location': location,
            'email': request.form['email'],
            'phone': request.form['phone'],
            'gstin': request.form['gstin']
        }
        print("New Supplier Details:", supplier)
        try:
            conn,cur=db_connection()
            query='''INSERT INTO suppliers_details(cont_name,saddress,email,phone_no,gstin) VALUES (%s,%s,%s,%s,%s)'''
            cur.execute(query,(supplier['name'],supplier['location'],supplier['email'],supplier['phone'],supplier['gstin']))
            conn.commit()
            conn.close()
            cur.close()
        except Exception as e:
            print(f"Error: {e}")
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/contractor_form.html')


def clients(table_name,column_name,):
    conn,cur=db_connection()
    query=f'''SELECT {column_name} from {table_name}'''
    cur.execute(query)
    datac=cur.fetchall()
    cur.close()
    conn.close()
    return [clients[0] for clients in datac]

@admin.route('/admin/newproject', methods=['GET', 'POST'])
@admin_required
def new_project():
    clientlist=clients("client_details","c_name")
    projectlist=clients("project_details","p_name")

    if request.method == 'POST':
        location = f"{request.form['p_address']}, {request.form['p_city']}, {request.form['p_state']} - {request.form['p_pincode']}"
        project = {
            'client_name': request.form['client_name'],
            'name': request.form['project_name'],
            'location': location,
            'start_date': request.form['start_date'],
            'completion_date': request.form['completion_date'],
            'work_type': request.form['work_type'],
            'project_type': request.form['project_type'],
            'services': request.form.getlist('services[]'),
            'design_fee': int(request.form.get('design_fee', 0)),
            'labour_fee': int(request.form.get('labour_fee', 0)),
            'material_cost': int(request.form.get('material_cost', 0)),
            'total_budget': int(request.form.get('total_budget', 0)),
            'description': request.form['description']
        }

        print("New Project Details:", project)

        conn, cur = db_connection()

        query = '''INSERT INTO project_details 
            (p_name, p_location, start_date, end_date, design_concept, desc_of_work, 
            c_name, project_type, services, design_fee, labour_fee, material_cost, 
            total_budget) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

        cur.execute(query, (
            project['name'],
            project['location'],
            project['start_date'],
            project['completion_date'],
            project['work_type'],
            project['description'],
            project['client_name'],
            project['project_type'],
            ','.join(project['services']),
            project['design_fee'],
            project['labour_fee'],
            project['material_cost'],
            project['total_budget']
        ))

        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/project_form.html', clients=clientlist, projects=projectlist)

@admin.route('/admin/newcontractor', methods=['GET', 'POST'])
@admin_required
def new_contractor():
    if request.method == 'POST':
        location = f"{request.form['address']}, {request.form['city']}, {request.form['state']} - {request.form['pincode']}"
        contractor = {
            'name': request.form['name'],
            'location': location,
            'email': request.form['email'],
            'phone': request.form['phone'],
            'gstin': request.form['gstin']
        }
        print("New Contractor Details:", contractor)
        conn,cur=db_connection()
        query='''INSERT INTO contractors_details(cont_name,caddress,email,phone_no,gstin) VALUES (%s,%s,%s,%s,%s)'''
        cur.execute(query,(contractor['name'],contractor['location'],contractor['email'],contractor['phone'],contractor['gstin']))
        conn.commit()
        conn.close()
        cur.close()
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/new_contractor_form.html')

@admin.route('/admin/supplier-payment', methods=['GET', 'POST'])
@admin_required
def supplier_payment():
    clientlist=clients("client_details","c_name")
    Supplierlist=clients("suppliers_details","cont_name")
    projectlist=clients("project_details","p_name")
    if request.method == 'POST':
        bill = {
            'supplier_name': request.form['supplier_name'],
            'client_name': request.form['client_name'],
            'project_name':request.form['project_name'],
            'bill_date': request.form['bill_date'],
            'amount': float(request.form.get('amount', 0)),
            'gst_percentage': float(request.form.get('gst_percentage', 0)),
            'gst_amount': float(request.form.get('gst_amount', 0)),
            'total_amount': float(request.form.get('total_amount', 0))
        }
        print("Supplier Bill Details:", bill)
        conn,cur=db_connection()
        query='''INSERT INTO supplier_bill_details(cont_name,clientname,p_name,bill_date,bill_amount,gst_percent,gst_amount,total_amount) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        '''
        cur.execute(query,(bill['supplier_name'],bill['client_name'],bill['project_name'],bill['bill_date'],bill['amount'],bill['gst_percentage'],bill['gst_amount'],bill['total_amount']))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/supplier_bill_entry.html',clients=clientlist,supplier=Supplierlist,projects=projectlist)

@admin.route('/admin/client-payment', methods=['GET', 'POST'])
@admin_required
def client_payment():
    clientlist=clients("client_details","c_name")
    projectlist=clients("project_details","p_name")
    if request.method == 'POST':
        payment = {
            'client_name': request.form['client_name'],
            'project_name': request.form['project_name'],
            'payment_date': request.form['payment_date'],
            'amount': float(request.form.get('amount', 0)),
            'mode_of_pay': request.form['mode_of_pay'],
            'cheque_no':"NULL",
            'transaction_id':"NULL"
        }
        
        if payment['mode_of_pay'] == 'cheque':
            payment['cheque_no'] = request.form.get('cheque_no')
        elif payment['mode_of_pay'] in ['upi', 'netbanking']:
            payment['transaction_id'] = request.form.get('transaction_id')
        conn,cur=db_connection()
        query = '''INSERT INTO payment_details 
            (clientname, project_name, date, amount, mode_of_payment, cheque_no, transaction_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)'''
    
        cur.execute(query, (
            payment['client_name'],
            payment['project_name'],
            payment['payment_date'],
            payment['amount'],
            payment['mode_of_pay'],
            payment['cheque_no'],
            payment['transaction_id']
        ))
        conn.commit()
        cur.close()
        conn.close()
        print("Client Payment Details:", payment)
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/client_payment.html',clients=clientlist,projects=projectlist)

@admin.route('/admin/contractor-payment', methods=['GET', 'POST'])
@admin_required
def contractor_payment():
    clientlist=clients("client_details","c_name")
    contractorlist=clients("contractors_details","cont_name")
    if request.method == 'POST':
        bill = {
            'contractor_name': request.form['contractor_name'],
            'client_name': request.form['client_name'],
            'project_name':request.form['project_name'],
            'bill_date': request.form['bill_date'],
            'amount': float(request.form.get('amount', 0)),
            'gst_percentage': float(request.form.get('gst_percentage', 0)),
            'gst_amount': float(request.form.get('gst_amount', 0)),
            'total_amount': float(request.form.get('total_amount', 0))
        }
        print("Contractor Bill Details:", bill)
        conn,cur=db_connection()
        query='''INSERT INTO contractor_bill_details(cont_name,clientname,p_name,bill_date,bill_amount,gst_percent,gst_amount,total_amount) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        '''
        cur.execute(query,(bill['contractor_name'],bill['client_name'],bill['project_name'],bill['bill_date'],bill['amount'],bill['gst_percentage'],bill['gst_amount'],bill['total_amount']))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/contractor_bill_entry.html',clients=clientlist,contractors=contractorlist)



def get_total_amount(client_name, project_name):
    conn, cur = db_connection()
    query = '''SELECT COALESCE(SUM(total_amount), 0) AS total_amount
               FROM contractor_bill_details
               WHERE clientname = %s and p_name = %s
               UNION ALL
               SELECT COALESCE(SUM(total_amount), 0)
               FROM supplier_bill_details
               WHERE clientname = %s and p_name = %s
               UNION ALL
               SELECT COALESCE(SUM(amount), 0) AS total_amount
               FROM payment_details
               WHERE clientname = %s and project_name = %s'''
    cur.execute(query, (client_name, project_name, client_name, project_name, client_name, project_name))
    total_amount = cur.fetchall()
    total_amount = [float(item[0]) for item in total_amount]
    cur.close()
    conn.close()
    return total_amount

@admin.route('/admin/projects/<uid>', methods=['GET', 'POST'])
@admin_required
def all_projects(uid):
    conn,cur=db_connection()
    query='''select p_name,p_location,start_date,end_date,design_concept,project_type FROM project_details WHERE c_name=%s'''
    cur.execute(query,(uid,))
    data=cur.fetchall()
    project_dict = [dict(p_name=row[0], p_location=row[1], start_date=row[2], end_date=row[3], design_concept=row[4], project_type=row[5]) for row in data]
    return render_template("admin/project_list.html", uid=uid, projects=project_dict)


@admin.route('/admin/projects/print/<uid>/<pname>', methods=['GET', 'POST'])
@admin_required
def printProject(uid, pname):
    try:
        conn, cur = db_connection()
        
        query = '''
            SELECT * FROM project_details 
            WHERE c_name = %s AND p_name = %s
        '''
        cur.execute(query, (uid, pname))
        project_data = cur.fetchone()
        
        if not project_data:
            return render_template("admin/error.html", error_message="Project not found")
        
        column_names = [desc[0] for desc in cur.description]
        project_dict = {column_names[i]: project_data[i] for i in range(len(column_names))}
        
        if project_dict.get('start_date'):
            project_dict['start_date'] = project_dict['start_date'].strftime('%Y-%m-%d')
        if project_dict.get('end_date'):
            project_dict['end_date'] = project_dict['end_date'].strftime('%Y-%m-%d')
        
        contractor_query = '''
            SELECT bill_date, cont_name, bill_amount, gst_amount, total_amount 
            FROM contractor_bill_details
            WHERE clientname = %s AND p_name = %s
            ORDER BY bill_date DESC
        '''
        cur.execute(contractor_query, (uid, pname))
        contractor_bills = []
        for row in cur.fetchall():
            contractor_bills.append({
                'bill_date': row[0].strftime('%Y-%m-%d') if row[0] else '',
                'cont_name': row[1],
                'bill_amount': row[2],
                'gst_amount': row[3],
                'total_amount': row[4]
            })
        
        supplier_query = '''
            SELECT bill_date, cont_name, bill_amount, gst_amount, total_amount 
            FROM supplier_bill_details
            WHERE clientname = %s AND p_name = %s
            ORDER BY bill_date DESC
        '''
        cur.execute(supplier_query, (uid, pname))
        supplier_bills = []
        for row in cur.fetchall():
            supplier_bills.append({
                'bill_date': row[0].strftime('%Y-%m-%d') if row[0] else '',
                'supplier_name': row[1],
                'bill_amount': row[2],
                'gst_amount': row[3],
                'total_amount': row[4]
            })
        
        supervisor_query = '''
            SELECT request_date, supervisor_name, project_name, amount, description 
            FROM supervisor_expenditure
            WHERE project_name = %s
            ORDER BY request_date DESC
        '''
        cur.execute(supervisor_query, (pname,))
        supervisor_expenses = []
        for row in cur.fetchall():
            supervisor_expenses.append({
                'date': row[0].strftime('%Y-%m-%d') if row[0] else '',
                'supervisor': row[1],
                'project': row[2],
                'amount': row[3],
                'description': row[4]
            })
        
        payment_query = '''
            SELECT date, amount, mode_of_payment, cheque_no, transaction_id
            FROM payment_details
            WHERE clientname = %s AND project_name = %s
            ORDER BY date DESC
        '''
        cur.execute(payment_query, (uid, pname))
        client_payments = []
        for row in cur.fetchall():
            client_payments.append({
                'payment_date': row[0].strftime('%Y-%m-%d') if row[0] else '',
                'amount': row[1],
                'mode_of_pay': row[2],
                'cheque_no': row[3],
                'transaction_id': row[4]
            })
        
        contractor_expenses = sum(bill['total_amount'] for bill in contractor_bills) if contractor_bills else 0
        supplier_expenses = sum(bill['total_amount'] for bill in supplier_bills) if supplier_bills else 0
        supervisor_expense_total = sum(expense['amount'] for expense in supervisor_expenses) if supervisor_expenses else 0
        payments_received = sum(payment['amount'] for payment in client_payments) if client_payments else 0
        
        total_expenses = contractor_expenses + supplier_expenses + supervisor_expense_total
        balance =  payments_received - total_expenses 
        
        financial_summary = {
            'contractor_expenses': contractor_expenses,
            'supplier_expenses': supplier_expenses,
            'supervisor_expenses': supervisor_expense_total,
            'total_expenses': total_expenses,
            'payments_received': payments_received,
            'balance': balance
        }
        
        cur.close()
        conn.close()
        
        return render_template(
            "admin/printdata.html", 
            uid=uid, 
            pname=pname,
            project_dict=project_dict,
            contractor_bills=contractor_bills,
            supplier_bills=supplier_bills,
            supervisor_expenses=supervisor_expenses,
            client_payments=client_payments,
            financial_summary=financial_summary
        )
    
    except Exception as e:
        print(f"Error in printProject: {e}")
        return render_template("admin/error.html", error_message=f"An error occurred: {str(e)}")

@admin.route('/admin/projects/audit/<uid>/<pname>', methods=['GET', 'POST'])
@admin_required
def printAudit(uid, pname):
    try:
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        if not from_date or not to_date:
            flash('Please select both From Date and To Date', 'error')
            return redirect(url_for('admin.all_projects', uid=uid))
            
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
        
        if from_date_obj > to_date_obj:
            flash('From Date cannot be greater than To Date', 'error')
            return redirect(url_for('admin.all_projects', uid=uid))
            
        one_year_from_now = datetime.now() + timedelta(days=365)
        if to_date_obj > one_year_from_now:
            flash('Date range cannot exceed 1 year', 'error')
            return redirect(url_for('admin.all_projects', uid=uid))
            
        conn, cur = db_connection()
        
        query = '''
            SELECT * FROM project_details 
            WHERE c_name = %s AND p_name = %s
        '''
        cur.execute(query, (uid, pname))
        project_data = cur.fetchone()
        
        if not project_data:
            flash('Project not found', 'error')
            return redirect(url_for('admin.all_projects', uid=uid))
            
        column_names = [desc[0] for desc in cur.description]
        project_dict = {column_names[i]: project_data[i] for i in range(len(column_names))}
        
        if project_dict.get('start_date'):
            project_dict['start_date'] = project_dict['start_date'].strftime('%Y-%m-%d')
        if project_dict.get('end_date'):
            project_dict['end_date'] = project_dict['end_date'].strftime('%Y-%m-%d')
            
        contractor_query = '''
            SELECT bill_date, cont_name, bill_amount, gst_amount, total_amount 
            FROM contractor_bill_details
            WHERE clientname = %s AND p_name = %s
            AND bill_date BETWEEN %s AND %s
            ORDER BY bill_date DESC
        '''
        cur.execute(contractor_query, (uid, pname, from_date, to_date))
        contractor_bills = []
        for row in cur.fetchall():
            contractor_bills.append({
                'bill_date': row[0].strftime('%Y-%m-%d') if row[0] else '',
                'cont_name': row[1],
                'bill_amount': row[2],
                'gst_amount': row[3],
                'total_amount': row[4]
            })
        
        supplier_query = '''
            SELECT bill_date, cont_name, bill_amount, gst_amount, total_amount 
            FROM supplier_bill_details
            WHERE clientname = %s AND p_name = %s
            AND bill_date BETWEEN %s AND %s
            ORDER BY bill_date DESC
        '''
        cur.execute(supplier_query, (uid, pname, from_date, to_date))
        supplier_bills = []
        for row in cur.fetchall():
            supplier_bills.append({
                'bill_date': row[0].strftime('%Y-%m-%d') if row[0] else '',
                'supplier_name': row[1],
                'bill_amount': row[2],
                'gst_amount': row[3],
                'total_amount': row[4]
            })
        
        supervisor_query = '''
            SELECT request_date, supervisor_name, project_name, amount, description 
            FROM supervisor_expenditure
            WHERE project_name = %s
            AND request_date BETWEEN %s AND %s
            ORDER BY request_date DESC
        '''
        cur.execute(supervisor_query, (pname, from_date, to_date))
        supervisor_expenses = []
        for row in cur.fetchall():
            supervisor_expenses.append({
                'date': row[0].strftime('%Y-%m-%d') if row[0] else '',
                'supervisor': row[1],
                'project': row[2],
                'amount': row[3],
                'description': row[4]
            })
        
        payment_query = '''
            SELECT date, amount, mode_of_payment, cheque_no, transaction_id
            FROM payment_details
            WHERE clientname = %s AND project_name = %s
            AND date BETWEEN %s AND %s
            ORDER BY date DESC
        '''
        cur.execute(payment_query, (uid, pname, from_date, to_date))
        client_payments = []
        for row in cur.fetchall():
            client_payments.append({
                'payment_date': row[0].strftime('%Y-%m-%d') if row[0] else '',
                'amount': row[1],
                'mode_of_pay': row[2],
                'cheque_no': row[3],
                'transaction_id': row[4]
            })
        
        contractor_expenses = sum(bill['total_amount'] for bill in contractor_bills) if contractor_bills else 0
        supplier_expenses = sum(bill['total_amount'] for bill in supplier_bills) if supplier_bills else 0
        supervisor_expense_total = sum(expense['amount'] for expense in supervisor_expenses) if supervisor_expenses else 0
        payments_received = sum(payment['amount'] for payment in client_payments) if client_payments else 0
        
        total_expenses = contractor_expenses + supplier_expenses + supervisor_expense_total
        balance = project_dict.get('total_budget', 0) - total_expenses
        
        financial_summary = {
            'contractor_expenses': contractor_expenses,
            'supplier_expenses': supplier_expenses,
            'supervisor_expenses': supervisor_expense_total,
            'total_expenses': total_expenses,
            'payments_received': payments_received,
            'balance': balance
        }
        
        cur.close()
        conn.close()
        
        return render_template(
            "admin/printdata.html", 
            uid=uid, 
            pname=pname,
            project_dict=project_dict,
            contractor_bills=contractor_bills,
            supplier_bills=supplier_bills,
            supervisor_expenses=supervisor_expenses,
            client_payments=client_payments,
            financial_summary=financial_summary,
            from_date=from_date,
            to_date=to_date
        )
                             
    except ValueError as e:
        flash('Invalid date format', 'error')
        return redirect(url_for('admin.all_projects', uid=uid))
    except Exception as e:
        flash('An error occurred while generating the audit report', 'error')
        return redirect(url_for('admin.all_projects', uid=uid))

@admin.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.index'))

def get_projects_by_client(client_name):
    conn, cur = db_connection()
    query = '''SELECT p_name FROM project_details WHERE c_name = %s'''
    cur.execute(query, (client_name,))
    projects = cur.fetchall()
    cur.close()
    conn.close()
    return [project[0] for project in projects]

@admin.route('/get-projects/<client_name>')
@admin_required
def get_projects(client_name):
    projects = get_projects_by_client(client_name)
    return {'projects': projects}

@admin.route('/admin/newsupervisor', methods=['GET', 'POST'])
@admin_required
def new_supervisor():
    if request.method == 'POST':
        location = f"{request.form['address']}, {request.form['city']}, {request.form['state']} - {request.form['pincode']}"
        supervisor = {
            'name': request.form['name'],
            'location': location,
            'email': request.form['email'],
            'phone': request.form['phone'],
            'password': generate_password_hash(request.form['password'])
        }
        print("New Supervisor Details:", supervisor)
        conn, cur = db_connection()
        query = '''INSERT INTO supervisor_details(super_name, super_address, super_email, phone_no, "super_Password") 
                  VALUES (%s, %s, %s, %s, %s)'''
        cur.execute(query, (
            supervisor['name'],
            supervisor['location'],
            supervisor['email'],
            supervisor['phone'],
            supervisor['password']
        ))
        query = '''INSERT INTO admin_info
                  (ausername, apass, apost) 
                  VALUES (%s, %s, %s)'''
        cur.execute(query,(supervisor['name'],supervisor['password'],"supervisor"))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/new_supervisor_form.html')

@admin.route('/admin/supervisor-dashboard', methods=['GET'])
@admin_required
def supervisor_dashboard():
    conn, cur = db_connection()
    supervisor_details={}
    try:
        query = '''SELECT s.super_name,s.super_address,s.super_email,s.phone_no FROM supervisor_details as s'''
        cur.execute(query)
        data = cur.fetchall()
        supervisor_details = [dict(
            super_name=row[0], 
            super_address=row[1], 
            super_email=row[2], 
            phone=row[3]
        ) for row in data]
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()
    return render_template('admin/supervisor_dashboard_admin.html',supervisor_details=supervisor_details)  

@admin.route('/admin/assign-tasks', methods=['GET', 'POST'])
@admin_required
def assign_task():
    query='''SELECT p_name from project_details'''
    conn,cur=db_connection()
    cur.execute(query)
    projects=cur.fetchall()
    query='''SELECT super_name from supervisor_details'''
    conn,cur=db_connection()
    cur.execute(query)
    supervisors=cur.fetchall()
    cur.close()
    conn.close()
    projects= [project[0] for project in projects]
    supervisors= [supervisor[0] for supervisor in supervisors]
    if request.method == 'POST':
        task = {
            'supervisor_name': request.form['supervisor-name'],
            'project_name': request.form['project-name'],
            'start_date': request.form['start_date'],
            'duration': request.form['duration'],
            'description': request.form['description']
        }
        conn, cur = db_connection()
        query = '''INSERT INTO task_assignments 
                  (supervisor_name, project_name, start_date, duration, description) 
                  VALUES (%s, %s, %s, %s, %s)'''
        cur.execute(query, (
            task['supervisor_name'],
            task['project_name'],
            task['start_date'],
            task['duration'],
            task['description']
        ))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin.supervisor_dashboard'))
    return render_template('admin/assign_task.html',projects=projects,supervisors=supervisors)

@admin.route('/admin/view-tasks', methods=['GET'])
@admin_required
def view_tasks():
    conn, cur = db_connection()
    query = '''
        SELECT t.supervisor_name, t.project_name, p.p_location, t.start_date,
        CASE 
            WHEN CURRENT_DATE < t.start_date THEN 'Pending'
            WHEN CURRENT_DATE > DATE(t.start_date + INTERVAL '1 DAY' * t.duration) THEN 'Completed'
            ELSE 'Ongoing'
        END as status, t.description
        FROM task_assignments t
        LEFT JOIN project_details p ON t.project_name = p.p_name
        ORDER BY t.start_date DESC
    '''
    cur.execute(query)
    tasks = [dict(
        supervisor_name=row[0],
        project=row[1],
        site_location=row[2],
        start_date=row[3].strftime('%Y-%m-%d') if row[3] else '',
        status=row[4],
        description=row[5]
    ) for row in cur.fetchall()]
    print(tasks)
    cur.close()
    conn.close()
    return render_template('admin/view_task.html',tasks=tasks)

@admin.route('/supervisor/dashboard/<supervisor_name>', methods=['GET', 'POST'])
@admin_required
def supervisor_dashboard_view(supervisor_name):
    if session.get('user_type') != 'supervisor' and session.get('username') != supervisor_name:
        return redirect(url_for('admin.index'))
    
    conn, cur = db_connection()
    
    query = '''
        SELECT t.task_id, t.project_name, p.p_location, t.start_date, 
               COALESCE(t.status, 
                    CASE 
                        WHEN CURRENT_DATE < t.start_date THEN 'Pending'
                        WHEN CURRENT_DATE > DATE(t.start_date + (t.duration || ' days')::INTERVAL) THEN 'Completed'
                        ELSE 'Ongoing'
                    END
               ) as status, t.description,
               COALESCE(t.remarks, '') as remarks
        FROM task_assignments t
        LEFT JOIN project_details p ON t.project_name = p.p_name
        WHERE t.supervisor_name = %s
        ORDER BY t.start_date DESC
    '''
    
    try:
        cur.execute(query, (supervisor_name,))
        tasks = [dict(
            task_id=row[0],
            project=row[1],
            site_location=row[2],
            start_date=row[3].strftime('%Y-%m-%d') if row[3] else '',
            status=row[4],
            description=row[5],
            remarks=row[6]
        ) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        tasks = []
    finally:
        cur.close()
        conn.close()
    
    return render_template('admin/sdashboard.html', supervisor_name=supervisor_name, tasks=tasks)

@admin.route('/admin/add-user', methods=['GET', 'POST'])
@admin_required
def add_admin_user():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin.admin_dashboard'))

    def get_users_and_supervisors():
        conn, cur = db_connection()
        query = '''SELECT ausername, apost FROM admin_info ORDER BY apost, ausername'''
        cur.execute(query)
        users = [dict(username=row[0], user_type=row[1]) for row in cur.fetchall()]
        
        supervisor_query = '''SELECT super_name FROM supervisor_details'''
        cur.execute(supervisor_query)
        supervisors = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        return users, supervisors

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        conn, cur = db_connection()

        if user_type == 'supervisor':
            supervisor_check = '''SELECT super_name FROM supervisor_details WHERE super_name = %s'''
            cur.execute(supervisor_check, (username,))
            is_valid_supervisor = cur.fetchone()

            if not is_valid_supervisor:
                cur.close()
                conn.close()
                users, supervisors = get_users_and_supervisors()
                return render_template('admin/add_user_form.html', 
                    error="Invalid supervisor name",
                    users=users, 
                    supervisors=supervisors)

            admin_check = '''SELECT ausername FROM admin_info WHERE ausername = %s AND apost = 'supervisor' '''
            cur.execute(admin_check, (username,))
            existing_admin = cur.fetchone()
            
            hashed_password = generate_password_hash(password)
            
            try:
                if existing_admin:
                    update_query = '''UPDATE admin_info SET apass = %s WHERE ausername = %s AND apost = 'supervisor' '''
                    cur.execute(update_query, (hashed_password, username))
                else:
                    insert_query = '''INSERT INTO admin_info (ausername, apass, apost) VALUES (%s, %s, 'supervisor')'''
                    cur.execute(insert_query, (username, hashed_password))
                
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for('admin.add_admin_user'))
            except Exception as e:
                print(f"Error managing supervisor: {e}")
                cur.close()
                conn.close()
                users, supervisors = get_users_and_supervisors()
                return render_template('admin/add_user_form.html', 
                    error=f"Error: {str(e)}",
                    users=users, 
                    supervisors=supervisors)
        else:
            check_query = '''SELECT ausername FROM admin_info WHERE ausername = %s'''
            cur.execute(check_query, (username,))
            existing_user = cur.fetchone()
            
            if existing_user:
                cur.close()
                conn.close()
                users, supervisors = get_users_and_supervisors()
                return render_template('admin/add_user_form.html', 
                    error="Username already exists",
                    users=users, 
                    supervisors=supervisors)

            try:
                hashed_password = generate_password_hash(password)
                insert_query = '''INSERT INTO admin_info (ausername, apass, apost) VALUES (%s, %s, %s)'''
                cur.execute(insert_query, (username, hashed_password, user_type))
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for('admin.add_admin_user'))
            except Exception as e:
                print(f"Error adding admin: {e}")
                cur.close()
                conn.close()
                users, supervisors = get_users_and_supervisors()
                return render_template('admin/add_user_form.html', 
                    error="Error adding admin",
                    users=users, 
                    supervisors=supervisors)

    users, supervisors = get_users_and_supervisors()
    return render_template('admin/add_user_form.html', users=users, supervisors=supervisors)

@admin.route('/admin/change-password', methods=['POST'])
@admin_required
def change_password():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin.admin_dashboard'))

    username = request.form['username']
    new_password = request.form['new_password']
    
    conn, cur = db_connection()
    try:
        hashed_password = generate_password_hash(new_password)
        query = '''UPDATE admin_info SET apass = %s WHERE ausername = %s'''
        cur.execute(query, (hashed_password, username))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin.add_admin_user'))
    except Exception as e:
        print(f"Error changing password: {e}")
        cur.close()
        conn.close()
        return redirect(url_for('admin.add_admin_user'))

@admin.route('/admin/delete-user/<username>')
@admin_required
def delete_user(username):
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin.admin_dashboard'))

    if username == session.get('username'):
        return redirect(url_for('admin.add_admin_user'))

    conn, cur = db_connection()
    try:
        query = '''DELETE FROM admin_info WHERE ausername = %s'''
        cur.execute(query, (username,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error deleting user: {e}")
        cur.close()
        conn.close()
    
    return redirect(url_for('admin.add_admin_user'))

@admin.route('/supervisor/update-task', methods=['POST'])
@admin_required
def update_task():
    if request.method == 'POST':
        task_id = request.form['task_id']
        supervisor_name = request.form['supervisor_name']
        status = request.form['status']
        remarks = request.form['remarks']

        conn, cur = db_connection()
        try:
            query = '''
                UPDATE task_assignments 
                SET status = %s, remarks = %s 
                WHERE task_id = %s
            '''
            cur.execute(query, (status, remarks, task_id))
            conn.commit()
        except Exception as e:
            print(f"Error updating task: {e}")
        finally:
            cur.close()
            conn.close()
        
        return redirect(url_for('admin.supervisor_dashboard_view', supervisor_name=supervisor_name))

@admin.route('/supervisor/expenditurelist/<supervisor_name>', methods=['GET', 'POST'])
@admin_required
def supervisor_expenditurelist(supervisor_name):
    if session.get('user_type') != 'supervisor' and session.get('username') != supervisor_name:
        return redirect(url_for('admin.index'))
    conn, cur = db_connection()
    expenditures = []
    try:
        expenditure_query = '''
            SELECT project_name, amount, description, request_date
            FROM supervisor_expenditure
            WHERE supervisor_name = %s
            ORDER BY request_date DESC
        '''
        cur.execute(expenditure_query, (supervisor_name,))
        expenditures = [dict(
            project=row[0],
            amount=row[1],
            description=row[2],
            date=row[3].strftime('%Y-%m-%d')
        ) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching data: {e}")
    finally:
        cur.close()
        conn.close()
    return render_template('admin/supervisor_expenditure_list.html', 
                         supervisor_name=supervisor_name,
                         expenditures=expenditures)



@admin.route('/supervisor/expenditure/<supervisor_name>', methods=['GET', 'POST'])
@admin_required
def supervisor_expenditure(supervisor_name):
    if session.get('user_type') != 'supervisor' and session.get('username') != supervisor_name:
        return redirect(url_for('admin.index'))
    
    conn, cur = db_connection()

    if request.method == 'POST':
        project_name = request.form['project_name']
        amount = request.form['amount']
        description = request.form['description']
        
        try:
            query = '''
                INSERT INTO supervisor_expenditure 
                (supervisor_name, project_name, amount, description)
                VALUES (%s, %s, %s, %s)
            '''
            cur.execute(query, (supervisor_name, project_name, amount, description))
            conn.commit()
        except Exception as e:
            print(f"Error submitting expenditure: {e}")
    projects = []
    expenditures = []
    try:
        project_query = '''
            SELECT DISTINCT project_name 
            FROM task_assignments 
            WHERE supervisor_name = %s
        '''
        cur.execute(project_query, (supervisor_name,))
        projects = [row[0] for row in cur.fetchall()]
        
        expenditure_query = '''
            SELECT project_name, amount, description, request_date
            FROM supervisor_expenditure
            WHERE supervisor_name = %s
            ORDER BY request_date DESC
        '''
        cur.execute(expenditure_query, (supervisor_name,))
        expenditures = [dict(
            project=row[0],
            amount=row[1],
            description=row[2],
            date=row[3].strftime('%Y-%m-%d')
        ) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching data: {e}")
    finally:
        cur.close()
        conn.close()
    
    return render_template('admin/supervisor_expenditure.html', 
                         supervisor_name=supervisor_name,
                         projects=projects,
                         expenditures=expenditures)

@admin.route('/admin/all-expenditures', methods=['GET'])
@admin_required
def all_expenditures():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin.index'))
    
    conn, cur = db_connection()
    expenditures = []
    
    try:
        exp_query = '''
            SELECT supervisor_name, project_name, amount, description, request_date
            FROM supervisor_expenditure
            ORDER BY request_date DESC
        '''
        cur.execute(exp_query)
        expenditures = [dict(
            supervisor=row[0],
            project=row[1],
            amount=row[2],
            description=row[3],
            date=row[4].strftime('%Y-%m-%d')
        ) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching expenditures: {e}")
    finally:
        cur.close()
        conn.close()
    
    return render_template('admin/all_expenditures.html', expenditures=expenditures)

@admin.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('error.html', message="CSRF token is missing or invalid. Please try again."), 400