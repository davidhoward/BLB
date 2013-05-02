import spark.KryoRegistrator
import com.esotericsoftware.kryo.Kryo

//would be good if this was automatically populated 
class MyRegistrator extends KryoRegistrator {
  override def registerClasses(kryo: Kryo) {
    //kryo.register(classOf[FeatureVec])
    kryo.register(classOf[CompressedFeatureVec])
    kryo.register(classOf[BootstrapData])
    // kryo.register(classOf[NGramRow])
  }
}

