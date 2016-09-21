class curry:
	'''This class is from Scott David Daniels' Recipe
	"Curry -- Associating Parameters with a Function"
	in the Python Cookbook'''

	def __init__(self, func, *args, **kwargs):
		self.func = func
		self.pending = args[:]
		self.kwargs = kwargs.copy()

	def __call__(self, *args, **kwargs):
		if kwargs and self.kwargs:
			kw = self.kwargs.copy()
			kw.update(kwargs)
		else:
			kw = kwargs or self.kwargs
		return self.func(*(self.pending + args), **kw)
