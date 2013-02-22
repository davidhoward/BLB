import java.io._
import scala.io._
//import java.lang.Double

object TestCustomDot {
	
def readVecs(filename: String): Array[Array[Double]]= {
    var f_in: FileInputStream = new FileInputStream(filename)
    var obj_in: ObjectInputStream = new ObjectInputStream(f_in)
    var modelMatrix: Array[Array[Double]] = obj_in.readObject().asInstanceOf[Array[Array[Array[Double]]]](0)
    return modelMatrix
}

def formatFeatureVec(input: String): FeatureVec={
        var vector = input.split(" ")
        var featureVec = new FeatureVec()
        featureVec.vec_weights = new Array[Double](vector.length-1)

        var first = true
        var num = 0
        var weight = 0.0
        var count = 0
        for (elem <- vector){
                if (first){
                        featureVec.tag = Integer.parseInt(elem)
                        first = false
                }
                else {
                        weight = java.lang.Double.parseDouble((elem.substring(elem.indexOf(':')+1, elem.length)))
                        featureVec.vec_weights(count) = weight
                        count += 1
                }
        }
        return featureVec
}

	def custom_dot_uncompressed_model(model:Array[Double], featureVec:FeatureVec): Double = {
		var featureVec_weights = featureVec.vec_weights
		var total =0.0
		var featureVec_weight = 0.0
		var model_weight = model(0)
		var i = 0		
		while (i < featureVec_weights.length){
			featureVec_weight = featureVec_weights(i)
			total += featureVec_weight * model(i+1)	
			i += 1
		}
		
		return total*model_weight
	}
	
	def main(args: Array[String]) {
	  var model = readVecs("e1double.model.java")
	  var fv_string = ""
	  scala.io.Source.fromFile("HVC000335.svmdat").getLines().foreach {   line => fv_string = line }
		//println("line here is:" + fv_string)
	  var fv = formatFeatureVec(fv_string)
	  println("Hello, world!")
	  var sub_model = new Array[Double](3)
	  var res = 0.0
	  for (sub_model <- model){
		res += custom_dot_uncompressed_model(sub_model, fv)
		}
	  res -= 0.97524881 
	  println("res is:", res)
	}
}
