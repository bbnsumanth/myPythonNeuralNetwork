import numpy as np
DEBUG = 0

class MyPyNN(object):

    def __init__(self, nOfInputDims=3, nOfHiddenLayers=1, \
                    hiddenLayerSizes=4, nOfOutputDims=2):

        if isinstance(hiddenLayerSizes, int):
            hiddenLayerSizes = [hiddenLayerSizes]

        if len(hiddenLayerSizes) != nOfHiddenLayers:
            print "Please specify sizes of hidden layers properly!!"
            return

        self.layerSizes = list(hiddenLayerSizes) #list() => deep copy
        self.layerSizes.insert(0, nOfInputDims)
        self.layerSizes.append(nOfOutputDims)

        # Network
        self.network = [{'weights':np.array(np.random.random(\
                        (self.layerSizes[layer-1]+1,self.layerSizes[layer])))} \
                        for layer in range(1,len(self.layerSizes))]

    def predict(self, X, visible=False):
        self.visible = visible
        inputs = self.preprocessInputs(X)

        if inputs.ndim!=1 and inputs.ndim!=2:
            print "X is not one or two dimensional, please check."
            return

        if DEBUG or self.visible:
            print "PREDICT:"
            print inputs

        for l, layer in enumerate(self.network):
            inputs = self.addBiasTerms(inputs)
            inputs = self.sigmoid(np.dot(inputs, layer['weights']))
            if DEBUG or self.visible:
                print "Layer "+str(l+1)
                print inputs
        
        return inputs

    def trainUsingGD(self, X, y, nIterations=1000, alpha=0.05, \
                        regLambda=0, visible=False):
        self.alpha = alpha
        self.regLambda = regLambda
        self.visible = visible
        for i in range(nIterations):
            print i
            self.forwardProp(X)
            self.backPropGradDescent(X, y)
            yPred = self.predict(X)
            print "accuracy = " + str((np.sum([np.all((yPred[i]>0.5)==y[i]) \
                                        for i in range(len(y))])).astype(float)/len(y))
        yPred = self.predict(X)
        if visible:
            print yPred

    def trainUsingSGD(self, X, y, nIterations=1000, minibatchSize=100, \
                        alpha=0.05, regLambda=0, visible=False):
        self.alpha = alpha
        self.regLambda = regLambda
        self.visible = visible
        X = self.preprocessInputs(X)
        y = self.preprocessOutputs(y)
        idx = range(len(X))
        if minibatchSize > len(X):
            minibatchSize = int(len(X)/10)+1
        for n in range(nIterations):
            print "Iteration "+str(n)+" of "+str(nIterations)
            np.random.shuffle(idx)
            idx = idx[:minibatchSize]
            miniX = X[idx]
            miniY = y[idx]
            a = self.forwardProp(miniX)
            if a==True:
                self.backPropGradDescent(miniX, miniY)
            else:
                return
            yPred = self.predict(X)
            if visible:
                print yPred
            print "accuracy = " + str((np.sum([np.all((yPred[i]>0.5)==y[i]) \
                                        for i in range(len(y))])).astype(float)/len(y))

    def forwardProp(self, inputs):
        inputs = self.preprocessInputs(inputs)
        print "Forward..."

        if inputs.ndim!=1 and inputs.ndim!=2:
            print "Input argument " + str(inputs.ndim) + \
                "is not one or two dimensional, please check."
            return False

        if (inputs.ndim==1 and len(inputs)!=self.layerSizes[0]) or \
            (inputs.ndim==2 and inputs.shape[1]!=self.layerSizes[0]):
            print "Input argument does not match input dimensions (" + \
                str(self.layerSizes[0]) + ") of network."
            return False
        
        if DEBUG or self.visible:
            print inputs

        for l, layer in enumerate(self.network):
            inputs = self.addBiasTerms(inputs)
            layer['outputs'] = self.sigmoid(np.dot(inputs, layer['weights']))
            inputs = np.array(layer['outputs'])
            if DEBUG or self.visible:
                print "Layer "+str(l+1)
                print inputs
        del inputs

        return True

    def backPropGradDescent(self, X, y):
        X = self.preprocessInputs(X)
        y = self.preprocessOutputs(y)
        print "...Backward"
        # Compute first error
        error = self.network[-1]['outputs'] - y

        if DEBUG or self.visible:
            print "error = self.network[-1]['outputs'] - y:"
            print error

        for l, layer in enumerate(reversed(self.network)):
            if DEBUG or self.visible:
                print "LAYER "+str(len(self.layerSizes)-1-l)
            
            predOutputs = layer['outputs']

            if DEBUG or self.visible:
                print "predOutputs"
                print predOutputs

            # delta = (z*(1-z))*(z - zHat) === nxneurons
            delta = np.multiply(np.multiply(predOutputs, 1 - predOutputs), \
                    error)/len(y)

            if DEBUG or self.visible:
                print "To compute error to be backpropagated:"
                print "del = predOutputs*(1 - predOutputs)*error :"
                print delta
                print "layer['weights']:"
                print layer['weights']

            # Compute new error to be propagated back (bias term neglected in backpropagation)
            error = np.dot(delta, layer['weights'][1:,:].T)

            if DEBUG or self.visible:
                print "backprop error = np.dot(del, layer['weights'][1:,:].T) :"
                print error

            # inputs === outputs from previous layer
            if l==len(self.network)-1:
                inputs = np.array(X)
            else:
                inputs = np.array(self.network[len(self.layerSizes)-2-l-1]['outputs'])
            inputs = self.addBiasTerms(inputs)
            
            if DEBUG or self.visible:
                print "To compute errorTerm:"
                print "inputs:"
                print inputs
                print "del:"
                print delta

            # errorTerm = (inputs.T).*(delta)
            # delta === nxneurons, inputs === nxprev, W === prevxneurons
            errorTerm = np.dot(inputs.T, delta)
            if errorTerm.ndim==1:
                errorTerm.reshape((len(errorTerm), 1))

            if DEBUG or self.visible:
                print "errorTerm = np.dot(inputs.T, del) :"
                print errorTerm
            
            # regularization term
            regWeight = np.zeros(layer['weights'].shape)
            regWeight[1:,:] = self.regLambda

            if DEBUG or self.visible:
                print "To update weights:"
                print "alpha*errorTerm:"
                print self.alpha*errorTerm
                print "regWeight:"
                print regWeight
                print "layer weights:"
                print layer['weights']
                print "regTerm = regWeight*layer['weights'] :"
                print regWeight*layer['weights']

            # Update weights
            layer['weights'] = layer['weights'] - \
                (self.alpha*errorTerm + np.multiply(regWeight,layer['weights']))
            
            if DEBUG or self.visible:
                print "Updated layer['weights'] = alpha*errorTerm + regTerm :"
                print layer['weights']

    def preprocessInputs(self, X):
        X = np.array(X, dtype=float)
        # if X is int
        if X.ndim==0:
            X = np.array([X])
        # if X is 1D
        if X.ndim==1:
            if self.layerSizes[0]==1: #if ndim=1
                X = np.reshape(X, (len(X),1))
            else: #if X is only 1 nd-ndimensional vector
                X = np.reshape(X, (1,len(X)))
        return X

    def preprocessOutputs(self, Y):
        Y = np.array(Y, dtype=float)
        # if Y is int
        if Y.ndim==0:
            Y = np.array([Y])
        # if Y is 1D
        if Y.ndim==1:
            if self.layerSizes[-1]==1:
                Y = np.reshape(Y, (len(Y),1))
            else:
                Y = np.reshape(Y, (1,len(Y)))
        return Y

    def addBiasTerms(self, X):
        if X.ndim==0 or X.ndim==1:
            X = np.insert(X, 0, 1)
        elif X.ndim==2:
            X = np.insert(X, 0, 1, axis=1)
        return X

    def sigmoid(self, z):
        return 1/(1 + np.exp(-z))
