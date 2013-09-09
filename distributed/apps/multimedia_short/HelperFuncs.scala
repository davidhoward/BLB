import java.util.ArrayList
import scala.collection.mutable.ListBuffer
import scala.collection.JavaConversions._
import java.io.ObjectInputStream

object HelperFuncs{

    def formatInputItem(input: Array[Array[Double]]): FeatureVec={
        var item = new EERItem()
        item.score = input
        return item 
    }

    def formatOutput(arr: Array[Double]): java.util.List[Double] ={
        var result_java_list: java.util.List[Double] = ListBuffer( arr: _* )
        return result_java_list
    }    
    
}