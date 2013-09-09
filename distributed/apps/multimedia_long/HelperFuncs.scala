import java.util.ArrayList
import scala.collection.mutable.ListBuffer
import java.io.FileInputStream
import scala.collection.JavaConversions._
import java.io.ObjectInputStream

object HelperFuncs{
    def formatInputItem(input: String): FeatureVec={
            var vector = input.split(" ")
            var featureVec = new FeatureVec()
            featureVec.vecWeights = new Array[Float](vector.length-1)

            var first = true
            var num = 0
            var weight:Float = 0.0.asInstanceOf[Float]
            var count = 0
            var i = 0
            var elem  = ""
            while (i < vector.length){
                elem = vector(i)
                if (first){
                    featureVec.tag = Integer.parseInt(elem)
                    first = false
                }
                else {
                    weight = java.lang.Float.parseFloat((elem.substring(elem.indexOf(':')+1, elem.length)))
                    featureVec.vecWeights(count) = weight
                    count += 1
                }
                i+=1
            }
            return featureVec
    }

    def formatOutput(arr: Array[Float]): java.util.List[Float] ={
        var result_java_list: java.util.List[Float] = ListBuffer( arr: _* )
        return result_java_list
    }    

    def dot(model:Array[Float], featureVec:FeatureVec): Float = {
        var featureVec_weights = featureVec.vecWeights
        var total =0.0.asInstanceOf[Float]
        var featureVec_weight = 0.0
        var model_weight = model(0)
        var i = 0
        while (i < featureVec_weights.length){
            total += featureVec_weights(i)* model(i+1)
            i += 1
        }
        return (total*model_weight).asInstanceOf[Float]
    }

    def readModels(filename: String): Array[Array[Array[Float]]]= {
        var f_in: FileInputStream = new FileInputStream(filename)
        var obj_in: ObjectInputStream = new ObjectInputStream(f_in)
        var modelMatrix: Array[Array[Array[Float]]] = obj_in.readObject().asInstanceOf[Array[Array[Array[Float]]]]
        return modelMatrix
    }

}