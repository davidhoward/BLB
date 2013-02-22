import java.util.ArrayList

// This class should be customized to allow for application-specific
// input to compute_estimate

class FeatureVec extends Serializable{
	var weight = 0
	var tag = 0
	var vec_weights = Array[Double]()
}

class CompressedFeatureVec extends Serializable{
	var weight = 0
	var tag = 0
	var vec_indices = Array[Int]()
	var vec_weights = Array[Double]()
}

class BootstrapData extends Serializable{
	var data = List[FeatureVec]()
	var models = new Array[Array[Array[Float]]](1)
}

