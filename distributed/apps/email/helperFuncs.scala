import scala.collection.mutable.ListBuffer
import java.io.FileInputStream
import scala.collection.JavaConversions._
import java.io.ObjectInputStream

object HelperFuncs {
    def formatInputItem(input: String): CompressedFeatureVec={
        var vector = input.split(" ")
        var featureVec = new CompressedFeatureVec()
        featureVec.vecIndices = new Array[Int](vector.length-1)
        featureVec.vecWeights = new Array[Double](vector.length-1)

        var first = true
        var num = 0
        var weight = 0
        var count = 0
        var i = 0
        var elem = ""
        while (i < vector.length){
            if (first){
                featureVec.tag = Integer.parseInt(elem)
                first = false
            }
            else {
                num = Integer.parseInt(elem.substring(0, elem.indexOf(':')))-1
                weight = Integer.parseInt(elem.substring(elem.indexOf(':')+1, elem.length))
                featureVec.vecIndices(count) = num
                featureVec.vecWeights(count) = weight
                count += 1
            }
            i+=1
        }
        return featureVec
    }

    def formatOutput[A](input: A): A= {return input}

    def dot(model: Array[Double] ,featureVec: CompressedFeatureVec): Double ={
        var featureVecIndices = featureVec.vecIndices
        var featureVecWeights = featureVec.vecWeights
        var total = 0.0
        var featureVecIndex = 0
        var featureVecWeight = 0.0
        var modelWeight = 0.0
        var i = 0
        try {
            while (i < featureVecIndices.length){
                featureVecIndex = featureVecIndices(i)
                featureVecWeight = featureVecWeights(i)
                modelWeight = model(featureVecIndex)
                total += featureVecWeight * modelWeight
                i += 1
            }
        } catch {
            case e: java.lang.ArrayIndexOutOfBoundsException =>
                println("Too large of feature value")
        }
        return total
    }

    def readModels(filename: String): Array[Array[Double]]= {
        var fileIn: FileInputStream = new FileInputStream(filename)
        var objIn: ObjectInputStream = new ObjectInputStream(fileIn)
        var modelMatrix: Array[Array[Double]] = objIn.readObject().asInstanceOf[Array[Array[Double]]]
        return modelMatrix
    }
}

