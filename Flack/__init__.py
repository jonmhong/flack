def run():
	os.environ['DATABASE_URL'] = 'sqlite://'
	os.environ['FLACK_CONFIG'] = 'testing'

	cov = coverage.Coverage(branch=True)
	