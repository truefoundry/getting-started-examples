import mlfoundry as mlf
import pandas as pd
import os
import argparse
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# total sales usa, total sales europe, yearly sales metrics

# plots yearly sales by country, monthly revenue, weekly revenue, revenue by product

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_usa", type=str, required=True)
parser.add_argument("--dataset_europe", type=str, required=True)
parser.add_argument("--ml_repo", type=str, required=True)

args = parser.parse_args()

client = mlf.get_client()
client.create_ml_repo(args.ml_repo)

run = client.create_run(ml_repo=args.ml_repo, run_name="preprocess-data")


def get_data_from_fqn(fqn):
    artifact_version = client.get_artifact_version_by_fqn(fqn)
    with tempfile.TemporaryDirectory() as temp_dir:
        artifact_version.download(temp_dir)
        # walk through the temp_dir and find a .csv file
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".csv"):
                    return pd.read_csv(os.path.join(root, file))

# Load the data
print("Loading the Data\n")
df_usa = get_data_from_fqn(args.dataset_usa)
df_europe = get_data_from_fqn(args.dataset_europe)

print("Data Loaded\n")

# Preprocess the data
print("Preprocessing the Data\n")
df = pd.concat([df_usa, df_europe])

# preprocess data
column_name_lower=[]
for i in df.columns:
    column_name_lower.append(i.lower()) 


#Rename column name by index 
for i in range(0, len(df.columns), 1):
    df=df.rename(columns={df.columns[i] : str(column_name_lower[i])})

df['orderdate']=pd.to_datetime(df['orderdate'])

df['monthvar']=df['orderdate'].dt.strftime('%b')
df['weekday']=df['orderdate'].dt.strftime('%a')

print("Data Preprocessing Complete\n")

# Log basic metrics

run.log_metrics(
    {
        "products_sold": len(df),
        "products_sold_usa": len(df_usa),
        "products_sold_europe": len(df_europe),
        "total_sales": df["sales"].sum(),
    }
)

# Find plot for yearly sales
yearly_sales=df.groupby(['year_id'])[['sales']].sum(numeric_only=True).reset_index()

plt.title('yearly_sales')
ax=sns.barplot(yearly_sales, x='year_id', y='sales', palette='pastel')
labels=[f'{value/1e6:.2f}M' for value in yearly_sales['sales']]

run.log_plots(
    {
        "yearly_sales": plt
    }
)

# Plot the productline sales and quantity ordered
print("Plotting the Data\n")

def barplotter(data, colname1, colname2, title, **kwargs):
    plt.title(title)
    sns.barplot(data=data, x=data[colname1], y=data[colname2], palette='Paired', **kwargs)
    plt.xticks(rotation=60)

# Plot each productline sales
sales_by_productline=df.groupby(['productline'])[['sales']].sum().reset_index()
barplotter(data=sales_by_productline, colname1='productline', colname2='sales', title='2003-2005 Revenue by Productline',errorbar=None)
#Ordered Q'ty by each productline
quantityordered_by_productline=df.groupby([ 'productline'])[['quantityordered']].sum().reset_index()
barplotter(data=quantityordered_by_productline, colname1='productline', colname2='quantityordered', title="2003-2005 Q'ty by Productline",errorbar=None)

run.log_plots(
    {
        "product_line": plt
    }
)

# Yearly sales by country

yearly_sales_by_country=df.groupby(['country', 'year_id'])[['sales']].sum().reset_index()

#Plot the revenue by year and country
plt.figure(figsize=(12,4))
plt.title('yearly_sales_by_country')
ax=sns.barplot(yearly_sales_by_country, x='country', y='sales',hue='year_id', palette='pastel')
xlabels=list(yearly_sales_by_country['country'].unique()) 
ax.set_xticklabels(labels=xlabels, rotation=90)

run.log_plots(
    {
        "yearly_sales_by_country": plt
    }
)


#Revenue by month
order=['Jan','Feb', 'Mar','Apr','May','Jun','Jul','Aug', 'Sep', 'Oct', 'Nov', 'Dec']

monthly_revenue=df.groupby(['month_id', 'year_id'])[['sales']].sum().reset_index()
ax=sns.barplot(data=monthly_revenue, x='month_id', y='sales', hue='year_id', palette='pastel')
plt.title('monthly_revenue')
ax.set_xlabel('month')
ax.set_xticklabels(order)

run.log_plots(
    {
        "monthly_revenue": plt
    }
)


# Log the final preprocessed data
print("Logging the Final Data\n")
df.to_csv('preprocessed_data.csv', index=False)

run.log_artifact(
    name="preprocessed_data",
    artifact_paths=[("preprocessed_data.csv",)]
)