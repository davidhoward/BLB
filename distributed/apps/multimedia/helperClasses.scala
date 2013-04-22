class FeatureVec extends Serializable{
	var weight = 0
	var tag = 0
	var vec_weights = Array[Double]()
}

class BootstrapData extends Serializable{
	var data = List[FeatureVec]()
	var models = new Array[Array[Array[Double]]](1)
}


