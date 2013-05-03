class CompressedFeatureVec extends Serializable{
	var weight = 0
	var tag = 0
	var vecIndices = Array[Int]()
	var vecWeights = Array[Double]()
}

class BootstrapData extends Serializable{
	var data = Array[CompressedFeatureVec]()
	var models = new Array[Array[Double]](1)
}

