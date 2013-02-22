import spark.KryoRegistrator
import com.esotericsoftware.kryo.Kryo

class MyRegistrator extends KryoRegistrator {
  override def registerClasses(kryo: Kryo) {
    kryo.register(classOf[FeatureVec])
    kryo.register(classOf[CompressedFeatureVec])
    kryo.register(classOf[BootstrapData])
  }
}

