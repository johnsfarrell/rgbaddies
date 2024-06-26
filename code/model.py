import keras
from keras.layers import \
     concatenate, Conv2DTranspose, Rescaling, BatchNormalization
from keras.applications import VGG19
from keras.layers import LeakyReLU
import hyperparameters as hp
from keras.losses import mean_squared_error as mse
from gaussian import gaussian_blur as blur

class Model():
    def __init__(self):
        
        inp = keras.Input(shape=(hp.img_size, hp.img_size, 3))
        
        vgg19 = VGG19(
            include_top=False,
            weights="imagenet",
            input_shape=(hp.img_size, hp.img_size, 3),
            input_tensor = inp
        )

        for layer in vgg19.layers:
            layer.trainable = False

        self.mod = vgg19.output
        b = Conv2DTranspose(filters=512, kernel_size=3, strides=2, activation=None, padding="same")(self.mod)
        b = LeakyReLU(alpha=0.1)(b)
        b = BatchNormalization()(b)
        self.mod = concatenate([b, vgg19.get_layer("block5_conv4").output])

        block_layer_sizes = [
            (512, "block4_conv4"),
            (256, "block3_conv4"),
            (128, "block2_conv2"),
            (64, "block1_conv2")
        ]

        for filters, layer_name in block_layer_sizes:
            b = Conv2DTranspose(filters=filters, kernel_size=3, strides=1, padding="same")(self.mod)
            b = LeakyReLU(alpha=0.1)(b)
            b = BatchNormalization()(b)
            b = Conv2DTranspose(filters=filters, kernel_size=3, strides=2, padding="same")(b)
            b = LeakyReLU(alpha=0.1)(b)
            b = BatchNormalization()(b)
           
            self.mod = concatenate([b, vgg19.get_layer(layer_name).output])

        self.mod = Conv2DTranspose(64, 3, padding="same")(self.mod)
        self.mod = LeakyReLU(alpha=0.1)(self.mod)
        self.mod = BatchNormalization()(self.mod)
        self.mod = Conv2DTranspose(2, 3, activation="sigmoid", padding="same")(self.mod)
        self.mod = Rescaling(scale=255.0, offset=-128)(self.mod)
        self.mod = keras.Model(inputs=inp, outputs=self.mod)
   
    def perceptual_loss(self, truth, predicted):
        """
        Calculates the perceptual loss between the truth and predicted images.
        """

        truth_blur_3 = blur(truth, (3,3))
        truth_blur_5 = blur(truth, (5,5))

        predicted_blur_3 = blur(predicted, (3,3))
        predicted_blur_5 = blur(predicted, (5,5))

        dist = mse(truth, predicted) ** 0.5
        dist_3 = mse(truth_blur_3, predicted_blur_3) ** 0.5
        dist_5 = mse(truth_blur_5, predicted_blur_5) ** 0.5
        
        return (dist + dist_3 + dist_5) / 3
