<%doc>
  This is a dummy impl file which allows the BLB
  C framework code to compile when user-defined
  reducer functions aren't supplied. A substitute
  for this file should generally be provided in real
  JIT compilation.
 
  @author David Howard
 
Templating varriables in use
 sub_n: The size of subsampled data
 n_bootstraps: the number of bootstraps to preform per subsample
 n_subsamples: the numer of subsamples to perform
 bootstrap_reducer: the name of the function with which to reduce bootstraps
 subsample_reducer: the name of the function with which to reduce subsamples
 classifier: the name of the function to calculate on the bootstraps
 
 attributes: a dictionary of optional flags that are passed into the classifier constructors
  with_cilk: whether or not the rendered functions should make use of cilk
 
Reducers defined by this file follow the interfaces

float compute_estimate( float* data, unsigned int* indicies, unsigned int size );

float reduce_bootstraps( float* data, unsigned int size );

float average( float * data, unsigned int size );
</%doc>

##Spits out the body of a mean calculation, sans declaration or return statement.
<%def name="mean(iter_direct, attributes)">
    <%
        i = 'i' if iter_direct else 'indicies[i]'
	access = 'data[ %s ]' % i
	iter = 'cilk_for' if ( attributes['with_cilk'] and iter_direct ) else 'for'
    %>
    float mean = 0.0;
    ${iter}( unsigned int i=0; i<size; i++ ){
       mean += ${access};
    }			 
    mean /= size;
</%def>

##Spits out the body of a standard deviation calculation, like unto mean defined above.
<%def name="stdev(iter_direct, attributes)">
    ${mean(iter_direct, attributes)}
      <%
	access = 'data[i]' if iter_direct else 'data[ indicies[i] ]'
	iter = 'cilk_for' if ( attributes['with_cilk'] and iter_direct ) else 'for'
      %>
    float stdev = 0.0;
    ${iter}( unsigned int i=0; i<size; i++ ){
       float datum = ${access};
       stdev += pow( datum - mean, 2 );
    }
    stdev = sqrt( stdev / size );
</%def>

##produce the classifier from the requested function
<%def name="make_classifier(func_name, attributes)">
    <%
        body = self.template.get_def(func_name).render(False, attributes)
    %>
float compute_estimate( float * data, unsigned int * indicies, unsigned int size ){
      	 ${body}
	 return ${func_name};
}
</%def>

##produce the bootstrap reducer from the requested function
<%def name="make_reduce_bootstraps( func_name, attributes )">
    <%
        body = self.template.get_def(func_name).render(True, attributes)
    %>
float reduce_bootstraps( float * data, unsigned int size ){
     	 ${body}
	 return ${func_name};
}
</%def>

##produce the subsample reducer from the requested function
<%def name="make_average( func_name, attributes )">
    <%
        body = self.template.get_def(func_name).render(True, attributes)
    %>
float average( float * data, unsigned int size ){
   	 ${ body }
	 return ${func_name};
}
</%def>


%if classifier is not UNDEFINED:
float compute_estimate( float* data, unsigned int* indicies,  unsigned int size ){
    ${classifier}
}
%elif use_classifier is not UNDEFINED:
    ${make_classifier(use_classifier, attributes)}
%endif

%if bootstrap_reducer is not UNDEFINED:
float reduce_bootstraps( float* data, unsigned int size ){
    ${bootstrap_reducer}
%elif use_bootstrap_reducer is not UNDEFINED:
    ${make_reduce_bootstraps(use_bootstrap_reducer, attributes)}
%endif

%if subsample_reducer is not UNDEFINED:
float average( float* data, unsigned int size ){
    ${subsample_reducer}
}
%elif use_subsample_reducer is not UNDEFINED:
    ${make_average(use_subsample_reducer, attributes)}
%endif