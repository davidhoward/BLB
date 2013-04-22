class CompressedFeatureVec extends Serializable{
	var weight = 0
	var tag = 0
	var vec_indices = Array[Int]()
	var vec_weights = Array[Double]()
}

class BootstrapData extends Serializable{
	var data = List[CompressedFeatureVec]()
	var models = new [Array[Array[Double]](1)
}

