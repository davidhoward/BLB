<%doc>
USING ARRAYS OF INDICIES INSTEAD OF COPPYING DATA
 Templating variables in use:
 sub_n: The size b(n) of data to be subsampled
 n_data: The initial data size
 n_subsamples: The number of subsamples to take
 n_bootstraps: The number of bootstraps to compute per subsample
 subsmaple_threshold: the probability parameter for the subsample rng
 seq_type: The python type of the data sequence, should be list or ndarray
</%doc>

void bootstrap( const unsigned int* in, unsigned int* out ){
    <%
        if bootstrap_unroll is UNDEFINED:
	    b = 1
	else:
	    b = bootstrap_unroll
    %>
  for( int i=0; i< ${sub_n/b}; i++ ){
    % for i in range(b):
    out[i*${b} + ${i}] = in[ rand() % ${sub_n} ];
    % endfor
  }
  % for i in range(sub_n % b):
  out[${sub_n-1-i}] = in[ rand() % ${sub_n} ];
  % endfor 
}

 char subsampled[ ${n_data} ];
 void subsample( unsigned int* out ){
 //  printf("About to subsample");
  int size_out = ${sub_n};
  while( size_out > 0 ){
    unsigned int index = rand() % ${n_data};
    if( subsampled[index] ){
      // Rely on not randomly selecting the same index
      // three times in one run
      subsampled[index] = 0;
    } else {
      subsampled[index] = 1;
      out[ ${sub_n} - size_out ] = index;
      size_out--;
    }
  }
//  for( int i=0; i<${sub_n}; i++ ){
//       subsampled[ out[i] ] = 0;
//  }
 }


<%doc>
const int threshold = (int)(${subsample_threshold}*RAND_MAX);
inline int flip( void ){
    return (rand() < threshold); 
}
unsigned int subsample_offset = 0;
void subsample ( unsigned int* out ){
    int size_out = ${sub_n};
    while( size_out > 0 ){
        if( flip() ){
	    out[ ${sub_n} - size_out ] = subsample_offset;
	    size_out--;
	}
	if( ++subsample_offset == ${n_data} ){
	    subsample_offset = 0;
	}
    }
}

</%doc>


## list is the default type.
%if seq_type == 'list': 

PyObject* compute_blb( PyObject*  data ){
  Py_INCREF(data);
  PyObject * py_arr = PyArray_FROM_OTF( data, NPY_FLOAT32, NPY_IN_ARRAY );
  Py_INCREF( py_arr );
  float * c_arr = (float*) PyArray_DATA( py_arr );

%elif seq_type == 'ndarray':

PyObject* compute_blb( PyObject* data ){
  Py_INCREF( data );
  float * c_arr = (float*) PyArray_DATA( data );

%endif
  memset( subsampled, 0, ${n_data} );
  

  //note that these are never cleared; We always fill them up
  //with the appropriate data before perform calculations on them.
  float * subsample_estimates = (float*) calloc( ${n_subsamples}, sizeof(float) );
  unsigned int * subsample_indicies = (unsigned int*) calloc( ${sub_n}, sizeof(unsigned int) );    
  unsigned int * bootstrap_indicies = (unsigned int*) calloc( ${sub_n}, sizeof(unsigned int) );
  float * bootstrap_estimates =  (float*) calloc( ${sub_n}, sizeof(float) );

  for( int i=0; i<${n_subsamples}; i++ ){

    subsample( subsample_indicies );
    cilk_for( int j=0; j<${n_bootstraps}; j++ ){

      bootstrap( subsample_indicies, bootstrap_indicies );
      bootstrap_estimates[j] = compute_estimate( c_arr, bootstrap_indicies, ${sub_n} );

    }
    subsample_estimates[i] = reduce_bootstraps( bootstrap_estimates, ${n_bootstraps} );
  }

  float theta = average( subsample_estimates, ${n_subsamples} );

  free( subsample_estimates );
  free( bootstrap_indicies );
  free( bootstrap_estimates );
  free( subsample_indicies );

%if seq_type is UNDEFINED or seq_type == 'list':
  Py_DECREF( py_arr );
%endif
  Py_DECREF( data );
  return PyFloat_FromDouble(theta);
}
