from flask import Flask, redirect, render_template, flash, request, session, g, jsonify, json
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug import datastructures
from models import SalesActual, SalesAvFDollars, SalesAvFPercent, connect_db, db, User, Product, bcrypt, MenuItemIngredients, Menu, MenuItem, SalesForecasting, SalesActual, SalesAvFPercent, SalesAvFDollars, HistoricalSalesInfo, Budget, Purchases, BeginningInventory, EndingInventory, InventoryResults
from forms import SignUpForm, SignInForm, NewMenuItemForm, NewMenuForm, WeeklyForecastForm, WeeklyActualsForm, NewProductForm, NewPurchaseForm, EndingInventoryForm
from datetime import date, timedelta
import requests
from decimal import Decimal
from api_logic import api_call
from sqlalchemy.exc import IntegrityError
import os
app=Flask(__name__)
# .replace("://" , "ql://" , 1)
app.config['SECRET_KEY']= os.environ.get('SECRET_KEY', 'secret')
app.config['SQLALCHEMY_DATABASE_URI']= os.environ.get('DATABASE_URL', 'postgresql:///food_cost_db').replace("://" , "ql://" , 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


debug=DebugToolbarExtension(app)

connect_db(app)

now = date.today()
tomorrow = now + timedelta(days = 4)
curr_user = 'username'

def set_week():
    """Used for budget/purchases to set the week of the purchase"""
    sales_weeks = HistoricalSalesInfo.query.filter(HistoricalSalesInfo.store_id == session['user_id'])
    week_nums = []
    for week in sales_weeks:
        week_nums.append(week.week)
    if week_nums == []:
        return 0
    else:
        return max(week_nums)






# ##################### Login/logout pages #########################





@app.route('/')
def landing_page():
    """Landing Page"""
    try:
        user = User.query.get(session['user_id'])
        if user:
            return redirect(f'/user/{user.id}')
    except KeyError:
        return render_template('home.html')

@app.route('/sign_up', methods = ['GET', 'POST'])
def sign_up():
    """Sign Up Page"""
    form = SignUpForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
            username = form.username.data,
            password = form.password.data,
            restaurant_name = form.restaurant_name.data,
            location = form.location.data or 'N/A',
            ideal_food_cost = form.ideal_food_cost.data
            )
            
        
        
            db.session.commit()
            session['username'] = user.username
            flash('User Created', 'success')
            return redirect(f'/user/{user.id}')
        except IntegrityError:
            flash('Username Already Exists')
            return redirect('/sign_up')

    return render_template('sign_up.html', form = form)


@app.route('/login', methods = ['GET', 'POST'])
def login():
    """Login for returning user"""
    form = SignInForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            session['username'] = user.username
            session['user_id'] = user.id
            flash(f"Welcome Back {user.username}!", 'success')
            
            return redirect(f'/user/{user.id}')
        flash('Invalid credentials', 'danger')


    return render_template('login.html', form = form)

@app.route('/logout')
def logout():
    """Logs user out of application"""
    session.pop('username')
    session.pop('user_id')
    flash('Successfully Logged Out', 'success')
    return redirect('/')


# ########################## User Pages ###############################

@app.route('/user/<int:user_id>')
def user_home_page(user_id):
    """Shows user home page"""
    if curr_user not in session:
        flash('Please login to access', 'warning')
        return redirect('/login')
   
    user = User.query.get_or_404(user_id)
    menus = Menu.query.filter(Menu.user_id == user.id)
    session['user_id'] = user.id
    return render_template('user_home_page.html', user=user, menus = menus)

@app.route('/edit_profile', methods = ['GET', 'POST'])
def edit_user_profile():
    """Edit user profile"""
    if curr_user not in session:
        flash('Please login to access', 'warning')
        return redirect('/login')


    user = User.query.get_or_404(session['user_id'])
    form = SignUpForm(obj = user)

    if form.validate_on_submit():
        username = user.username
        password = form.password.data
        if User.authenticate(username, password) == False:
            flash('Password does not match. Cannot change password', 'danger')
            return redirect(f'/user/{user.id}')
        else:
            user.username = form.username.data
            user.restaurant_name = form.restaurant_name.data,
            user.location = form.location.data or 'N/A',
            user.ideal_food_cost = form.ideal_food_cost.data
            session['username'] = user.username
            db.session.add(user)
            db.session.commit()
            week_budget = Budget.query.filter(Budget.user_id == user.id)
            budget = week_budget.one_or_none()
            if budget != None:
                sales_forecast = SalesForecasting.query.filter(SalesForecasting.store_id == user.id)
                forecast = sales_forecast[0]
                new_user_info = User.query.get(session['user_id'])
                budget.starting_budget = round((new_user_info.ideal_food_cost / 100) * forecast.weekly_total , 2)
                db.session.commit()
        flash('Changes Successful', 'success')
        return redirect(f'/user/{user.id}')


    return render_template('edit_user.html', form = form, user = user)


# ########################## Menu Pages ####################################

@app.route('/new_menu', methods = ['GET', 'POST'])
def create_new_menu():
    """Create new menu for user"""
    if curr_user not in session:
        flash('Please login to access', 'warning')
        return redirect('/login')

    form = NewMenuForm()
    user = User.query.get_or_404(session['user_id'])
    if form.validate_on_submit():
        new_menu = Menu(
            user_id = user.id,
            menu_name = form.menu_name.data ,
            menu_description = form.menu_description.data
        )
        db.session.add(new_menu)
        db.session.commit()
        flash('Created New Menu', 'success')
        return redirect(f'/user/{user.id}')

    return render_template('new_menu.html', form = form, user = user)
    


@app.route('/new_menu_items/<int:menu_id>', methods = ['GET', 'POST'])
def create_new_menu_items(menu_id):
    """Create new menu items for user"""
    if curr_user not in session:
        flash('Please login to access', 'warning')
        return redirect('/login')

    form = NewMenuItemForm()
    curr_menu = Menu.query.get_or_404(menu_id)
    menu_items = MenuItem.query.all()
    user = User.query.get_or_404(session['user_id'])
    if request.method == 'POST':
        data = request.json
        
        menu_item = MenuItem(
            user_id = user.id,
            menu_id = curr_menu.id,
            menu_item_name = data['menu_item_name'],
            menu_description = data['menu_description'],
            menu_price = data['menu_price'],
            plate_price = 0.00
        )
        db.session.add(menu_item)
        db.session.commit()
  
        flash('Created New Menu Item')
        return redirect(f'/new_menu_items/{curr_menu.id}')
        

    return render_template('new_menu_item.html', form = form, menu=curr_menu, user = user, menu_items = menu_items)

@app.route('/api/delete_menu_item/<int:id>/<item_name>' , methods = ['DELETE'])
def delete_menu_item(id, item_name):
    """Delete an item from the menu"""
    menu_item = MenuItem.query.filter(MenuItem.menu_id == id , MenuItem.menu_item_name == item_name)
    item = menu_item[0]
    db.session.delete(item)
    db.session.commit()
    return jsonify(message = 'deleted')

@app.route('/api/menu/<int:id>', methods = ['DELETE'])
def delete_menu(id):
    """Delete a menu"""
    menu = Menu.query.get_or_404(id)
    db.session.delete(menu)
    db.session.commit()
    return jsonify(message = 'deleted')









#  ############################# Product Pages #############################


@app.route('/menu_item_page/<int:id>/<item_name>', methods = ['GET', 'POST'])
def item_page(id,item_name):
    """Displays a single menu item where a user can add ingredients"""
    # item = MenuItem.query.get(id)
    # menu_id = item.menu_id
    name = MenuItem.query.filter(MenuItem.menu_id == id , MenuItem.menu_item_name == item_name)
    menu_item_1 = name[0]
    item = menu_item_1.id
    user = User.query.get_or_404(session['user_id'])
    form = NewProductForm()
    ingredients = MenuItemIngredients.query.filter(MenuItemIngredients.menu_item_id == item)
    if form.validate_on_submit():
        item_name = form.product_name.data
        item_list = Product.query.filter(Product.name == item_name)
        all_matches = item_list.all()
        if len(all_matches) == 0:
            try:
                product_search = api_call(item_name)
                new_product = Product(
                name = product_search[0],
                price = product_search[1]
                 )
                db.session.add(new_product)
                db.session.commit()
                menu_item = MenuItemIngredients(
                product_id = new_product.id,
                menu_item_id = item.id
                )
                db.session.add(menu_item)
                db.session.commit()
            except ValueError:
                flash('Product Not Found', 'info')
                return redirect(f'/menu_item_page/{menu_item_1.menu_id}/{menu_item_1.menu_item_name}')
            
            return redirect(f'/menu_item_page/{menu_item_1.menu_id}/{menu_item_1.menu_item_name}')
        else:
            menu_item = MenuItemIngredients(
                product_id = all_matches[0].id,
                menu_item_id = item
            )
            db.session.add(menu_item)
            db.session.commit()
            return redirect(f'/menu_item_page/{menu_item_1.menu_id}/{menu_item_1.menu_item_name}')
    
    return render_template('menu_item.html', item = item, user = user, form = form, ingredients = ingredients, menu_item = menu_item_1)


@app.route('/api/delete_product/<int:product_id>', methods = ['DELETE'])
def delete_product(product_id):
    """Delete a prodcut from a menu item"""
    product = MenuItemIngredients.query.get(product_id)
   
    db.session.delete(product)
    db.session.commit()

    return jsonify(message = 'deleted')




# ########################### Inventory Pages##################################

@app.route('/inventory_home_page/<int:user_id>', methods = ['GET', 'DELETE'])
def inventory_home_page(user_id):
    """Home page for the users inventory"""

    user = User.query.get(user_id)
    week = set_week()
    purchases = Purchases.query.filter(Purchases.user_id == user.id , Purchases.week_purchased == week +1)
    wtd_purchases = 0
    for purchase in purchases:
            wtd_purchases += purchase.amount_spent
    


    budget_list = Budget.query.filter(Budget.user_id == user.id)
    
    budget_list[0].weekly_purchases = round(wtd_purchases ,2 )
    budget_list[0].remaining_budget = round(budget_list[0].starting_budget - wtd_purchases , 2)
    db.session.commit()
    logged_budget = Budget.query.filter(Budget.user_id == user.id)
    budget = logged_budget[0]
    return render_template('inventory_home_page.html', user = user, budget = budget, purchases = purchases)
  
        

@app.route('/add_purchase', methods = ['GET', 'POST'])
def add_purchase():
    """Page for user to add in product purchased"""
    user = User.query.get(session['user_id'])
    form = NewPurchaseForm()
    week = set_week()
    
    purchases = Purchases.query.filter(Purchases.user_id == user.id, Purchases.week_purchased == week + 1)

    if form.validate_on_submit():
        product = form.product_name.data
        amount = form.units_purchased.data
        date_purchsed = form.date_purchased.data
        product_query = Product.query.filter(Product.name == product)
        all_matches = product_query.all()
        if len(all_matches) == 0:
            try:
                product_search = api_call(product)
                new_product = Product(
                name = product_search[0],
                price = product_search[1]
                 )
                db.session.add(new_product)
                db.session.commit()
            except:
                flash('Could Not Locate Product, try a different product name', 'info')
                return redirect('/add_purchase')
        new_purchase = Purchases(
            user_id = user.id,
            product_id = product_query[0].id,
            amount_spent = round(product_query[0].price * amount, 2),
            amount_purchased = amount,
            date_purchased = date_purchsed,
            week_purchased = week + 1
        )
        db.session.add(new_purchase)
        db.session.commit()
        flash('Purchase Added', 'success')
        return redirect('/add_purchase')
    return render_template('add_purchase.html', user = user, form = form, purchases = purchases)

@app.route('/api/delete_purchase/<int:id>' , methods = ['DELETE'])
def delete_purchase(id):
    """Delete a purchase"""
    purchase = Purchases.query.get(id)
    db.session.delete(purchase)
    db.session.commit()
    return jsonify(message = 'deleted')

@app.route('/inventory_count/<int:user_id>', methods = ['GET', 'POST', 'DELETE'])
def inventory_count_page(user_id):
    """Page for the user to enter their inventory count"""

    user = User.query.get(user_id)
    curr_week = set_week()
    form = EndingInventoryForm()
    products = [(p.id, p.name) for p in Product.query.all()]
    end_inv = EndingInventory.query.filter(EndingInventory.user_id == user.id , EndingInventory.week == curr_week)
    form.product.choices = products

    
    if form.validate_on_submit():
        product_id = form.product.data
        ending_amount = form.amount_on_hand.data
        
        product = Product.query.get(product_id)
        ending_inv_result = EndingInventory(
            user_id = user.id,
            product_id = product_id,
            ending_item_count = ending_amount,
            ending_dollar_amount = round(product.price * ending_amount, 2),
            week = curr_week
        )
    
        db.session.add(ending_inv_result)
        db.session.commit()
        flash('Added Ending Count', 'success')
        return redirect(f'/inventory_count/{user.id}')
    
   

    
    return render_template('inventory_count.html', user = user, form = form, end_inv = end_inv)


@app.route('/api/delete_entry/<int:id>', methods = ['DELETE'])
def delete_inv_entry(id):
    """Delete an ending inventory entry"""
    user = User.query.get(session['user_id'])
    entry = EndingInventory.query.get(id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify(message='deleted')


@app.route('/first_check_submit')
def first_check():
    """First check before submitting full inventory results"""

    user = User.query.get(session['user_id'])
    return render_template('first_check.html', user = user)
    
@app.route('/submit_full_count')
def submit_full_count():
    """User able to submit full count for the week. This will turn current ending inventory results into next weeks beginning results and create weekly results numbers"""

    user = User.query.get(session['user_id'])
    week = set_week()
    sales_nums = HistoricalSalesInfo.query.filter(HistoricalSalesInfo.store_id == session['user_id'], HistoricalSalesInfo.week == week)
    sales = sales_nums.all()
    end_inv = EndingInventory.query.filter(EndingInventory.user_id == session['user_id'], EndingInventory.week == week)
    purchases = Purchases.query.filter(Purchases.user_id == session['user_id'], Purchases.week_purchased == week)
    first_purchase = purchases.all()
    total_purchases = 0
    for purchase in first_purchase:
        total_purchases+=purchase.amount_spent

    old_beg_inv = BeginningInventory.query.filter(BeginningInventory.user_id == session['user_id'], BeginningInventory.week == week)
    first_beg_inv = old_beg_inv.all()
    beg_inv_total = 0
    for amount in first_beg_inv:
        beg_inv_total+=amount.beginning_dollar_amount

    all_endings = end_inv.all()
    total_ending = 0
    for amount in all_endings:
        total_ending+=amount.ending_dollar_amount

    for inv in all_endings:
        new_beg = BeginningInventory(
            user_id = user.id,
            product_id = inv.product_id,
            beginning_item_count = inv.ending_item_count,
            beginning_dollar_amount = inv.ending_dollar_amount,
            week = week + 1)
        db.session.add(new_beg)
        db.session.commit()


    inv_res = InventoryResults(
        user_id = session['user_id'],
        actual_food_cost = ((beg_inv_total + total_purchases) - total_ending) / sales[0].actual_total,
        actual_vs_goal_food_cost = (((beg_inv_total + total_purchases) - total_ending) / sales[0].actual_total) - user.ideal_food_cost,
        week = week + 1
    )
    db.session.add(inv_res)
    db.session.commit()

        


    flash('Inventory Results Saved', 'success')
    return redirect(f'/inventory_home_page/{user.id}')

@app.route('/historic_inventory_results/<int:user_id>')
def historic_resutls(user_id):
    """Shows user inventory restults"""

    user = User.query.get(user_id)
    res = InventoryResults.query.filter(InventoryResults.user_id == user.id)
    weekly_res = res.all()
    return render_template('inventory_results.html', user = user, weekly_res = weekly_res)

@app.route('/week_results/<int:week>')
def week_results(week):
    """Shows the week selected results"""
    user = User.query.get(session['user_id'])
    res = InventoryResults.query.filter(InventoryResults.week == week, InventoryResults.user_id == user.id)
    week_results = res.all()
    week_res = week_results[0]
    return render_template('weekly_inv_results.html', user = user, week_res = week_res)




# ########################## Sales Forecasting Pages ###########################


@app.route('/sales', methods = ['GET', 'DELETE'])
def sales_home_page():
    """Users sales home page that shows sales forecasts and data"""

    if curr_user not in session:
        flash('Please login to access', 'warning')
        return redirect('/login')
    user = User.query.get_or_404(session['user_id'])
    last_week = set_week()
    week = last_week + 1
    try:
        sales_forecast = SalesForecasting.query.filter(SalesForecasting.store_id == user.id)
        forecast = sales_forecast[0]
        sales_actuals = SalesActual.query.filter(SalesActual.store_id == user.id)
        actuals = sales_actuals[0]
        sales_avf_dollars = SalesAvFDollars.query.filter(SalesAvFDollars.store_id == user.id)
        avf_dollars = sales_avf_dollars[0]
        sales_avf_percent = SalesAvFPercent.query.filter(SalesAvFPercent.store_id == user.id)
        avf_percent = sales_avf_percent[0]
        return render_template('sales_homepage.html', user = user, forecast = forecast, actuals = actuals, avf_dollars = avf_dollars, avf_percent = avf_percent)
    except IndexError:
        forecast = None
        actuals = None
        avf_dollars = None
        avf_percent = None
        return render_template('sales_homepage.html' , user = user , forecast = forecast, actuals = actuals , avf_dollars = avf_dollars , avf_percent = avf_percent)

@app.route('/update_forecast', methods = ['GET', 'POST'])
def update_forecast():
    """Allows user to update their forecast for the week"""


    if curr_user not in session:
        flash('Please login to access', 'warning')
        return redirect('/login')


    user = User.query.get_or_404(session['user_id'])
    week= set_week()

    sales_avf_percent = SalesAvFPercent.query.filter(SalesAvFPercent.store_id == user.id)
    avf_percent = sales_avf_percent.one_or_none()
    beg_inv = BeginningInventory.query.filter(BeginningInventory.user_id == user.id)
    if len(beg_inv.all()) == 0:
            products_list = Product.query.all()
            for product in products_list:
                new_beg_inv = BeginningInventory(
                    user_id = user.id,
                    product_id = product.id,
                    beginning_item_count = 0,
                    beginning_dollar_amount = 0,
                    week = week + 1
                )
                db.session.add(new_beg_inv)
                db.session.commit()
    try:
        sales_forecasted_week = SalesForecasting.query.filter(SalesForecasting.store_id == user.id)
        forecasted_week = sales_forecasted_week[0]
        form = WeeklyForecastForm(obj = forecasted_week)
        set_budget = Budget.query.filter(Budget.user_id == session['user_id'])
        sales_avf_dollars = SalesAvFDollars.query.filter(SalesAvFDollars.store_id == user.id)
        avf_dollars = sales_avf_dollars[0]
        if form.validate_on_submit():
            
            forecasted_week.monday = form.monday.data
            forecasted_week.tuesday = form.tuesday.data
            forecasted_week.wednesday = form.wednesday.data
            forecasted_week.thursday = form.thursday.data
            forecasted_week.friday = form.friday.data
            forecasted_week.saturday = form.saturday.data
            forecasted_week.sunday = form.sunday.data
            forecasted_week.weekly_total = form.monday.data + form.tuesday.data + form.wednesday.data + form.thursday.data + form.friday.data + form.saturday.data + form.sunday.data
            db.session.commit()
            set_budget[0].starting_budget = (user.ideal_food_cost / 100) * (form.monday.data + form.tuesday.data + form.wednesday.data + form.thursday.data + form.friday.data + form.saturday.data + form.sunday.data)
            avf_dollars.monday = -(forecasted_week.monday)
            avf_dollars.tuesday = -(forecasted_week.tuesday)
            avf_dollars.wednesday = -(forecasted_week.wednesday)
            avf_dollars.thursday = -(forecasted_week.thursday)
            avf_dollars.friday = -(forecasted_week.friday)
            avf_dollars.saturday = -(forecasted_week.saturday)
            avf_dollars.sunday = -(forecasted_week.sunday)
            avf_dollars.weekly_total = -(forecasted_week.weekly_total)
               
            db.session.commit()
            flash('Forecast Updated', 'success')
            return redirect('/sales')
    except:
        form = WeeklyForecastForm()
    
        if form.validate_on_submit():
            forecast = SalesForecasting(
            store_id = user.id,
            monday = form.monday.data,
            tuesday = form.tuesday.data,
            wednesday = form.wednesday.data,
            thursday = form.thursday.data,
            friday = form.friday.data,
            saturday = form.saturday.data,
            sunday = form.sunday.data,
            weekly_total = form.monday.data + form.tuesday.data + form.wednesday.data + form.thursday.data + form.friday.data + form.saturday.data + form.sunday.data
        )
            db.session.add(forecast)
            db.session.commit()
            
            weekly_budget = Budget.query.filter(Budget.user_id == session['user_id'])
            all_responses = weekly_budget.all()
            if len(all_responses) == 0:
                    new_budget = Budget(
                    user_id = user.id,
                    starting_budget = (user.ideal_food_cost / 100) * forecast.weekly_total,
                    weekly_purchases = 0,
                    remaining_budget = round((user.ideal_food_cost / 100) * forecast.weekly_total , 2)
            )
                    db.session.add(new_budget)
                    db.session.commit()
            else:
                    db.session.delete(all_responses[0])
                    db.session.commit()
                    new_budget = Budget(
                    user_id = user.id,
                    starting_budget = (user.ideal_food_cost / 100) * forecast.weekly_total,
                    weekly_purchases = 0,
                    remaining_budget = round((user.ideal_food_cost / 100) * forecast.weekly_total , 2)
                    )
                    db.session.add(new_budget)
                    db.session.commit()
            old_actuals = SalesActual.query.filter(SalesActual.store_id == user.id)
            actuals = old_actuals.one_or_none()
            if actuals == None:
                sales_actuals = SalesActual(
                store_id = user.id,
                monday = 0,
                tuesday = 0,
                wednesday = 0,
                thursday = 0,
                friday = 0,
                saturday = 0,
                sunday = 0,
                weekly_total = 0)
                db.session.add(sales_actuals)
                db.session.commit()

            old_avf_dollars = SalesAvFDollars.query.filter(SalesAvFDollars.store_id == user.id)
            avf_dollars = old_avf_dollars.one_or_none()
            forecast_list = SalesForecasting.query.filter(SalesForecasting.store_id == user.id)
            new_forecast = forecast_list.one_or_none()
            if avf_dollars == None:
                sales_diff_dollars = SalesAvFDollars(
                store_id = user.id,
                monday = -(new_forecast.monday),
                tuesday = -(new_forecast.tuesday),
                wednesday = -(new_forecast.wednesday),
                thursday = -(new_forecast.thursday),
                friday = -(new_forecast.friday),
                saturday = -(new_forecast.saturday),
                sunday = -(new_forecast.sunday),
                weekly_total = -(new_forecast.weekly_total)
            )
                db.session.add(sales_diff_dollars)
                db.session.commit()
            
            old_avf_percent = SalesAvFPercent.query.filter(SalesAvFPercent.store_id == user.id)
            avf_percent = old_avf_percent.one_or_none()
            if avf_percent == None:
                sales_diff_percent = SalesAvFPercent(
                store_id = user.id,
                monday = -100,
                tuesday = -100,
                wednesday = -100,
                thursday = -100, 
                friday = -100,
                saturday = -100,
                sunday = -100, 
                weekly_total = -100
            )
            db.session.add(sales_diff_percent)
            db.session.commit()
       
        
            flash('Forecast Submitted', 'success')
            return redirect('/sales')
    return render_template('update_forecast.html', form = form, user = user)

@app.route('/update_actuals', methods = ['GET', 'POST'])
def update_actuals():
    """Allow user to update current weekly actual sales"""

    if curr_user not in session:
        flash('Please login to access', 'warning')
        return redirect('/login')
    user = User.query.get_or_404(session['user_id'])
    week = set_week()
    sales_actuals = SalesActual.query.filter(SalesActual.store_id == user.id)
    actuals = sales_actuals[0]
    form = WeeklyActualsForm(obj = actuals)
    return render_template('update_actuals.html', form = form, user = user)



@app.route('/insert_actuals', methods = ['POST'])
def insert_actuals():
    user = User.query.get(session['user_id'])
    week = set_week()
    sales_actuals = SalesActual.query.filter(SalesActual.store_id == user.id)
    actuals = sales_actuals[0]
    sales_forecast = SalesForecasting.query.filter(SalesForecasting.store_id == user.id)
    forecast = sales_forecast[0]
    sales_avf_dollars = SalesAvFDollars.query.filter(SalesAvFDollars.store_id == user.id)
    avf_dollars = sales_avf_dollars[0]
    sales_avf_percent = SalesAvFPercent.query.filter(SalesAvFPercent.store_id == user.id)
    avf_percent = sales_avf_percent[0]
    
    form = WeeklyActualsForm()
    if form.validate_on_submit():
      
        actuals.store_id = user.id
        actuals.monday = form.monday.data
        actuals.tuesday = form.tuesday.data
        actuals.wednesday = form.wednesday.data
        actuals.thursday = form.thursday.data
        actuals.friday = form.friday.data
        actuals.saturday = form.saturday.data
        actuals.sunday = form.sunday.data
        actuals.weekly_total = form.monday.data + form.tuesday.data + form.wednesday.data + form.thursday.data + form.friday.data + form.saturday.data + form.sunday.data
        db.session.commit()
        new_actual_sales = SalesActual.query.filter(SalesActual.store_id == user.id)
        new_actuals = new_actual_sales[0]
   
        avf_dollars.store_id = user.id
        avf_dollars.monday = new_actuals.monday -forecast.monday
        avf_dollars.tuesday = new_actuals.tuesday - forecast.tuesday,
        avf_dollars.wednesday = new_actuals.wednesday -forecast.wednesday,
        avf_dollars.thursday = new_actuals.thursday -forecast.thursday,
        avf_dollars.friday = new_actuals.friday -forecast.friday,
        avf_dollars.saturday = new_actuals.saturday -forecast.saturday,
        avf_dollars.sunday = new_actuals.sunday -forecast.sunday,
        avf_dollars.weekly_total = (new_actuals.monday -forecast.monday) + (new_actuals.tuesday - forecast.tuesday) + (new_actuals.wednesday -forecast.wednesday) + (new_actuals.thursday -forecast.thursday) + (new_actuals.friday -forecast.friday) + (new_actuals.saturday -forecast.saturday) + (new_actuals.sunday -forecast.sunday)
        
        db.session.commit()
        new_avf_dollars_sales = SalesAvFDollars.query.filter(SalesAvFDollars.store_id == user.id)
        new_avf_dollars = new_avf_dollars_sales[0]
      
        avf_percent.store_id = user.id
        avf_percent.monday = round((new_avf_dollars.monday / forecast.monday) * 100, 2)
        avf_percent.tuesday = round((new_avf_dollars.tuesday / forecast.tuesday) * 100, 2)
        avf_percent.wednesday = round((new_avf_dollars.wednesday / forecast.wednesday) * 100,2)
        avf_percent.thursday = round((new_avf_dollars.thursday / forecast.thursday) * 100, 2)
        avf_percent.friday = round((new_avf_dollars.friday / forecast.friday) * 100, 2)
        avf_percent.saturday = round((new_avf_dollars.saturday / forecast.saturday) * 100, 2)
        avf_percent.sunday = round((new_avf_dollars.sunday / forecast.sunday) * 100, 2)
        avf_percent.weekly_total = round((((new_avf_dollars.monday / forecast.monday) * 100) + ((new_avf_dollars.tuesday / forecast.tuesday) * 100) + ((new_avf_dollars.wednesday / forecast.wednesday) * 100) + ((new_avf_dollars.thursday / forecast.thursday) * 100) + ((new_avf_dollars.friday / forecast.friday) * 100) + ((new_avf_dollars.saturday / forecast.saturday) * 100) + ((new_avf_dollars.sunday / forecast.sunday) * 100)) / 7 , 2)
        
        db.session.commit()
 
    return redirect('/sales')

@app.route('/confirm_sales_submit')
def comfirm_sales():
    """Page for user to confirm submitting sales"""
    user = User.query.get(session['user_id'])
    return render_template('confirm_sales.html', user = user)


@app.route('/submit_sales', methods = ['GET','POST'])
def submit_sales():
    """Submits sales to historical data table and resets currents back to zero"""

    user = User.query.get(session['user_id'])
    sales_forecast = SalesForecasting.query.filter(SalesForecasting.store_id == user.id)
    forecast = sales_forecast[0]
    sales_actuals = SalesActual.query.filter(SalesActual.store_id == user.id)
    actuals = sales_actuals[0]
    sales_avf_dollars = SalesAvFDollars.query.filter(SalesAvFDollars.store_id == user.id)
    avf_dollars = sales_avf_dollars[0]
    sales_avf_percent = SalesAvFPercent.query.filter(SalesAvFPercent.store_id == user.id)
    avf_percent = sales_avf_percent[0]
    logged_sales = HistoricalSalesInfo.query.filter(HistoricalSalesInfo.store_id == user.id).all()
    if len(logged_sales) == 0:
        week = 1
    else: 
        week = len(logged_sales) + 1
    historic_sales = HistoricalSalesInfo(
        store_id = user.id,
        date_logged = now,
        monday_forecasted = forecast.monday,
        tuesday_forecasted = forecast.tuesday,
        wednesday_forecasted = forecast.wednesday,
        thursday_forecasted = forecast.thursday,
        friday_forecasted = forecast.friday,
        saturday_forecasted = forecast.saturday,
        sunday_forecasted = forecast.sunday,
        monday_actual = actuals.monday,
        tuesday_actual = actuals.tuesday,
        wednesday_actual = actuals.wednesday,
        thursday_actual = actuals.thursday,
        friday_actual = actuals.friday,
        saturday_actual = actuals.saturday,
        sunday_actual = actuals.sunday,
        forecasted_total = forecast.weekly_total,
        actual_total = actuals.weekly_total,
        week = week
    )

    db.session.add(historic_sales)
    db.session.commit()
    weekly_data = [forecast, actuals, avf_dollars, avf_percent]
    for i in weekly_data:
        db.session.delete(i)
    db.session.commit()
    flash('Sales reset and logged into historical sales data', 'success')
    return redirect('/sales')

@app.route('/historic_sales/<int:user_id>')
def historic_sales(user_id):
    """Page that lists all users weeks of logged data for them to choose from"""
    user = User.query.get(user_id)
    h_sales = HistoricalSalesInfo.query.filter(HistoricalSalesInfo.store_id == user_id).all()
    

    return render_template('historic_sales.html', user = user, h_sales = h_sales)


@app.route('/historical/week_<int:week>')
def weekly_historic_details(week):
    """Displays a page of a specific historical weekly sales data"""
    user = User.query.get(session['user_id'])
    sales_week = HistoricalSalesInfo.query.filter((HistoricalSalesInfo.store_id == user.id) & (HistoricalSalesInfo.week == week)).first()

    return render_template('historic_week_sales_data.html', user = user, sales_week = sales_week)

