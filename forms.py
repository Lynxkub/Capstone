from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, IntegerField, PasswordField, FloatField, DateField, SelectField
from wtforms import validators
from wtforms.validators import InputRequired, Optional
from wtforms.widgets.core import Input




# ####################### User Forms #################################

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    restaurant_name = StringField('Restaurant Name', validators=[InputRequired()])
    location = StringField('Location')
    ideal_food_cost = FloatField('Ideal Food Cost', validators=[InputRequired()])


class SignInForm(FlaskForm):
   username = StringField('Username', validators=[InputRequired()])
   password = PasswordField('Password', validators=[InputRequired()])



# ########################### Menu Forms ###############################

class NewMenuForm(FlaskForm):
    menu_name = StringField('Menu Name', validators=[InputRequired()])
    menu_description = StringField('Menu Description')

class NewMenuItemForm(FlaskForm):
    menu_item_name = StringField('Menu Item Name', validators=[InputRequired()])
    menu_description = StringField('Menu Description')
    menu_price = FloatField('Menu Price', validators=[InputRequired()])


# ######################## Product Forms ##############################

class NewProductForm(FlaskForm):
    product_name = StringField("Product Name", validators=[InputRequired()])


class NewPurchaseForm(FlaskForm):
    product_name = StringField("Product Name", validators=[InputRequired()])
    units_purchased = IntegerField('Amount Purchased', validators = [InputRequired()])
    date_purchased = DateField('Date Purchased', validators = [InputRequired()])

#  ######################### Forecasting/Sales  Forms #########################


class WeeklyForecastForm(FlaskForm):
    monday = IntegerField('Monday', validators=[InputRequired()])
    tuesday = IntegerField('Tuesday', validators=[InputRequired()])
    wednesday = IntegerField('Wednesday', validators=[InputRequired()])
    thursday = IntegerField('Thursday', validators=[InputRequired()])
    friday = IntegerField('Friday', validators=[InputRequired()])
    saturday = IntegerField('Saturday', validators=[InputRequired()])
    sunday = IntegerField('Sunday', validators=[InputRequired()])

class WeeklyActualsForm(FlaskForm):
    monday = IntegerField('Monday')
    tuesday = IntegerField('Tuesday')
    wednesday = IntegerField('Wednesday')
    thursday = IntegerField('Thursday')
    friday = IntegerField('Friday')
    saturday = IntegerField('Saturday')
    sunday = IntegerField('Sunday')


# ############################ Inventory Forms ##############################

class EndingInventoryForm(FlaskForm):
    product = SelectField('Product', coerce=int)
    amount_on_hand = FloatField('Ending Count', validators = [InputRequired()])