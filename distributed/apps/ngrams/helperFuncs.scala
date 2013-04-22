import java.util.ArrayList
import scala.collection.mutable.ListBuffer
import java.io.FileInputStream
import scala.collection.JavaConversions._
import java.io.ObjectInputStream
import java.util.List

object HelperFuncs{
	def formatInputItem(input: String): NGramRow ={
	    var ngramrow = new NGramRow()
	    ngramrow.weight = 0
	    ngramrow.year_counts = input
	    return ngramrow
	}

	def formatOutput(arr: Array[Double]): java.util.List[Double] ={
		var result_java_list: java.util.List[Double] = ListBuffer( arr: _* )
		return result_java_list
	}
}