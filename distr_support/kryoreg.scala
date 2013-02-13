import spark.KryoRegistrator
import com.esotericsoftware.kryo.Kryo

class MyRegistrator extends KryoRegistrator {
  override def registerClasses(kryo: Kryo) {
    kryo.register(classOf[Email])
    kryo.register(classOf[EmailBootstrapData])
    kryo.register(classOf[MultimediaBootstrapData])
    kryo.register(classOf[Multimedia])
  }
}

