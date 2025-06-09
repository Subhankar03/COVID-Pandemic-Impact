import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from millify import millify
from nbconvert import HTMLExporter
from streamlit_lottie import st_lottie


# Page title and configurations
st.set_page_config(
	page_title='COVID-19 Pandemic Impact',
	page_icon='static/virus.png',
	layout='wide'
)

# Load custom CSS
# st.html('style.css')
st.html('style.css')

# Title and icon
col1, col2 = st.columns((.06, .94), vertical_alignment='center')
col1.image('static/virus.png', width=64)
col2.title('COVID-19 Pandemic Impact')
st.write('')

# Use README.md to create overview section
with open('README.md', encoding='utf-8') as f:
	md = f.read()
with open('COVID Pandemic Analysis.ipynb', encoding='utf-8') as f:
	nb_html, _ = HTMLExporter().from_file(f)
	nb = f.read()

# Load and cache data
@st.cache_data
def load_dataset():
	deaths = pd.read_csv('dataset/covid_deaths.csv')
	vaccinations = pd.read_csv('dataset/covid_vaccinations.csv')
	data = pd.concat([deaths, vaccinations.drop(columns=['iso_code', 'continent', 'location', 'date'])], axis=1)
	data = data[['continent', 'location', 'date', 'population', 'new_cases', 'total_cases',
				 'new_vaccinations', 'people_vaccinated', 'hospital_beds_per_thousand',
				 'hosp_patients', 'new_deaths', 'total_deaths', 'stringency_index']]
	data['date'] = pd.to_datetime(data['date'])
	return data, {'Covid Deaths': deaths, 'Covid Vaccinations': vaccinations}
df, dfs = load_dataset()

# Add 3 tabs: Overview, Dashboard, Notebook
overview, notebook, dashboard = st.tabs([
	':material/description: Overview',
	':material/code: Notebook',
	':material/space_dashboard: Dashboard'
])


# Overview tab
with overview:
	col1, col2 = st.columns((.7, .3))
	# Project overview, Objective
	col1.markdown(md[md.find('## Project'): md.find('## Methodology')])
	with col2:  # Add a lottie animation
		st_lottie('https://lottie.host/7c4b2218-3f16-4bde-aefa-ee16fe5e3e22/0r4SFAW0m7.json')
	
	# Expander to show the dataset
	with st.expander('See the dataset', icon=':material/table:'):
		st.caption('''
            The dataset contains information about COVID-19 cases, vaccinations, and deaths across different countries,
            along with other related metrics like hospitalization rates and policy stringency.
            ''')
		# Show user selected table
		@st.fragment
		def show_dataset():
			table = st.segmented_control(
				'Table:', ['Covid Deaths', 'Covid Vaccinations'],
				default='Covid Deaths', label_visibility='collapsed'
			)
			if table: st.dataframe(dfs[table], hide_index=True)
		show_dataset()
	
	# Methodology, Key Takeaways, Conclusion
	st.markdown(md[md.find('## Methodology'):])


# Notebook tab
with notebook:
	components.html(nb_html, height=9200, scrolling=True)
	st.divider()
	# Button to download the notebook
	st.download_button(
		label='Download notebook', data=nb,
		file_name='COVID Pandemic Analysis.ipynb',
		icon=':material/download:',
		on_click='ignore'
	)


# Dashboard tab
with (dashboard):
	# Top level metrics
	global_stats = {
		':orange[Total Cases]': millify(df['total_cases'].max()),
		':green[Total Vaccinations]': millify(df['people_vaccinated'].max()),
		':orange[Hospitalized Patients]': millify(df['hosp_patients'].max()),
		':red[Total Deaths]': millify(df['total_deaths'].max())
	}
	for col, label, value in zip(st.columns(4), global_stats.keys(), global_stats.values()):
		col.metric(label, value, border=True)
	
	# Map section
	countries = df[df.continent.notna()].groupby(['location', 'population'], as_index=False)
	countries = countries[['total_cases', 'people_vaccinated', 'total_deaths']].max()
	countries['cases_pct'] = countries.total_cases / countries.population * 100
	countries['vaccinations_pct'] = countries.people_vaccinated / countries.population * 100
	countries['deaths_pct'] = countries.total_deaths / countries.population * 100
	countries.loc[countries.vaccinations_pct > 100, 'vaccinations_pct'] = 100
	
	# Visualization options
	@st.fragment
	def show_map():
		col1, _ = st.columns((1, 3))
		map_metric = col1.selectbox(
			"Choose Metric",
			options=["Cases (% of Population)", "Vaccinations (% of Population)", "Deaths (% of Population)"],
			index=0
		)
		col1, col2 = st.columns((.7, .3))
		
		# Create map and bar chart based on selection
		if map_metric == "Cases (% of Population)":
			color_col = 'cases_pct'
			title = 'COVID-19 Cases as % of Population'
			hover = {'location': True, 'cases_pct': ':.2f', 'total_cases': True, 'population': True}
		elif map_metric == "Vaccinations (% of Population)":
			color_col = 'vaccinations_pct'
			title = 'COVID-19 Vaccinations as % of Population'
			hover = {'location': True, 'vaccinations_pct': ':.2f', 'people_vaccinated': True, 'population': True}
		else:
			color_col = 'deaths_pct'
			title = 'COVID-19 Deaths as % of Population'
			hover = {'location': True, 'deaths_pct': ':.2f', 'total_deaths': True, 'population': True}
		
		# Choropleth Map
		fig_map = px.choropleth(
			countries, locations='location', locationmode='country names',
			color=color_col,
			color_continuous_scale='Oranges' if "Case" in title else 'Greens' if "Vaccination" in title else 'Reds',
			title=title, hover_data=hover
		).update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0},
						paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
		col1.plotly_chart(fig_map, use_container_width=True)
		
		# Top 5 bar chart
		top5 = countries.sort_values(by=color_col, ascending=False).head(5)
		fig_bar = px.bar(
			top5, x='location', y=color_col,
			title=f"Top 5 Countries by {map_metric}",
			labels={color_col: map_metric, 'location': 'Country'},
			color=color_col, color_continuous_scale='Oranges' if "Case" in title else 'Greens' if "Vaccination" in title else 'Reds'
		).update_layout(yaxis_title=map_metric, margin=dict(t=40), coloraxis_showscale=False,
						paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
		col2.plotly_chart(fig_bar, use_container_width=True)
	show_map()
	
	# Time series visualization options
	@st.fragment
	def show_line_and_bubble():
		col1, col2 = st.columns((1, 3), vertical_alignment='bottom')
		ts_type = col1.selectbox(
			"Select Data Type",
			options=["New Cases", "New Deaths", "New Vaccinations", "Total Cases", "Total Deaths", "Total Vaccinations"]
		)
		# Create time series plot based on selection
		if ts_type == "New Cases":
			y_column = 'new_cases_avg'
			title = 'New COVID-19 Cases'
			y_title = 'New Cases (7-day avg)'
		elif ts_type == "New Deaths":
			y_column = 'new_deaths_avg'
			title = 'New COVID-19 Deaths'
			y_title = 'New Deaths (7-day avg)'
		elif ts_type == "New Vaccinations":
			y_column = 'new_vaccinations_avg'
			title = 'New COVID-19 Vaccinations'
			y_title = 'New Vaccinations (7-day avg)'
		elif ts_type == "Total Cases":
			y_column = 'total_cases'
			title = 'Total COVID-19 Cases'
			y_title = 'Total Cases'
		elif ts_type == "Total Deaths":
			y_column = 'total_deaths'
			title = 'Total COVID-19 Deaths'
			y_title = 'Total Deaths'
		else:
			y_column = 'people_vaccinated'
			title = 'Total COVID-19 Vaccinations'
			y_title = 'Total Vaccinations'
		
		# Add country filter
		available_countries = sorted(df['location'].unique().tolist())
		selected_countries = col2.multiselect(
			"Select Countries",
			options=available_countries,
			default=["United States", "India", "Brazil", "United Kingdom", "Russia"]
		)
		
		# Time series analysis section
		if selected_countries:
			time_df = df[df['location'].isin(selected_countries)]
		else:
			# If no countries selected, use top 5 by total cases
			top_countries = df.groupby('location')['total_cases'].max().nlargest(5).index.tolist()
			time_df = df[df['location'].isin(top_countries)]
		
		# Group by location and date
		time_series = time_df.groupby(['location', 'date']).agg({
			'new_cases': 'sum',
			'new_deaths': 'sum',
			'new_vaccinations': 'sum',
			'total_cases': 'max',
			'total_deaths': 'max',
			'people_vaccinated': 'max'
		}).reset_index()
		
		# Apply rolling average to smooth the data
		for location in time_series['location'].unique():
			mask = time_series['location'] == location
			time_series.loc[mask, 'new_cases_avg'] = time_series.loc[mask, 'new_cases'].rolling(7).mean()
			time_series.loc[mask, 'new_deaths_avg'] = time_series.loc[mask, 'new_deaths'].rolling(7).mean()
			time_series.loc[mask, 'new_vaccinations_avg'] = time_series.loc[mask, 'new_vaccinations'].rolling(7).mean()
		
		col1, col2 = st.columns(2)
		fig_ts = px.line(
			time_series, x='date', y=y_column, color='location', title=title,
			labels={'date': 'Date', y_column: y_title, 'location': 'Country'}
		).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
		col1.plotly_chart(fig_ts, use_container_width=True)
	
		# Mortality analysis section
		mortality_df = df.groupby('location').agg({
			'total_cases': 'max',
			'total_deaths': 'max',
			'population': 'first'
		}).reset_index()
		
		# Handle NaN values
		mortality_df['total_cases'] = mortality_df['total_cases'].fillna(0)
		mortality_df['total_deaths'] = mortality_df['total_deaths'].fillna(0)
		mortality_df['population'] = mortality_df['population'].fillna(1)
		
		# Calculate rates but avoid division by zero
		mortality_df['mortality_rate'] = np.where(
			mortality_df['total_cases'] > 0,
			mortality_df['total_deaths'] / mortality_df['total_cases'] * 100,
			0
		)
		
		mortality_df['cases_per_million'] = np.where(
			mortality_df['population'] > 0,
			mortality_df['total_cases'] / mortality_df['population'] * 1_000_000,
			0
		)
		
		mortality_df['deaths_per_million'] = np.where(
			mortality_df['population'] > 0,
			mortality_df['total_deaths'] / mortality_df['population'] * 1_000_000,
			0
		)
		
		# Filter to show only countries with significant number of cases
		mortality_df = mortality_df[mortality_df['total_cases'] > 10000].sort_values('mortality_rate', ascending=False)
		
		# Create a scatter plot showing mortality vs cases per million
		# Make sure we're not using any rows with NaN values that could cause problems
		plot_mortality_df = mortality_df.dropna(subset=['cases_per_million', 'mortality_rate', 'deaths_per_million'])
		
		fig_mortality = px.scatter(
			plot_mortality_df,
			x='cases_per_million',
			y='mortality_rate',
			size='deaths_per_million',
			color='deaths_per_million',
			hover_name='location',
			color_continuous_scale='OrRd',
			size_max=50,
			title='COVID-19 Mortality Rate vs. Case Rate',
			labels={
				'cases_per_million': 'Cases per Million',
				'mortality_rate': 'Mortality Rate (%)',
				'deaths_per_million': 'Deaths per Million'
			}
		).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
		if selected_countries:
			# Highlight selected countries on the plot
			for country in selected_countries:
				if country in mortality_df['location'].values:
					country_data = mortality_df[mortality_df['location'] == country]
					fig_mortality.add_annotation(
						x=country_data['cases_per_million'].values[0],
						y=country_data['mortality_rate'].values[0],
						text=country,
						showarrow=True,
						arrowhead=1
					)
		col2.plotly_chart(fig_mortality, use_container_width=True)
	show_line_and_bubble()

	# Comparative analysis section
	@st.fragment
	def show_scatter_plot():
		col1, col2, _ = st.columns((1, 1, 2))
		# Let user select x-axis variable and y-axis variable
		x_variable = col1.selectbox(
			"X-Axis Variable",
			options=["total_cases", "people_vaccinated", "stringency_index", "hospital_beds_per_thousand"],
			format_func=lambda x: x.replace('_', ' ').title(),
			index=0
		)
		y_variable = col2.selectbox(
			"Y-Axis Variable",
			options=["total_deaths", "hospital_beds_per_thousand", "stringency_index"],
			format_func=lambda x: x.replace('_', ' ').title(),
			index=0
		)
		# Prepare data
		latest_data = df.sort_values('date').groupby('location').last().reset_index()
		
		# Create scatter plot - handle missing values first
		scatter_data = latest_data.copy()
		
		# Fill NaN values with 0 for the variables we're using
		scatter_data[x_variable] = scatter_data[x_variable].fillna(0)
		scatter_data[y_variable] = scatter_data[y_variable].fillna(0)
		scatter_data['population'] = scatter_data['population'].fillna(1000000)  # Default population if missing
		
		# Remove rows where continent is NaN
		scatter_data = scatter_data.dropna(subset=['continent'])
		
		# Scatter plot to show relationship between variables
		fig_scatter = px.scatter(
			scatter_data,
			x=x_variable,
			y=y_variable,
			size="population",
			color="continent",
			hover_name="location",
			size_max=60,
			title=f'Relationship between {x_variable.replace("_", " ").title()} and {y_variable.replace("_", " ").title()}',
			labels={
				x_variable: x_variable.replace('_', ' ').title(),
				y_variable: y_variable.replace('_', ' ').title(),
				'continent': 'Continent',
				'population': 'Population'
			}
		).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
		st.plotly_chart(fig_scatter, use_container_width=True)
	show_scatter_plot()
	
	# Add date range information
	date_range = f"{df['date'].min().strftime('%B, %Y')} - {df['date'].max().strftime('%B, %Y')}"
	st.info(f"Data period is limited to {date_range}", icon=':material/info:', width=400)