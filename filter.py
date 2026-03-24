import pandas as pd

# Read the CSV file
df = pd.read_csv('slcl_resources.csv')

# Filter rows where type == 'Subscription Database'
filtered_df = df[df['type'] == 'Subscription Database']

# Save the filtered data to a new CSV file
filtered_df.to_csv('subscription_resources.csv', index=False)
